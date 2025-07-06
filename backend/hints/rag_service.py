import os
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.db.models import Q
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# LangChain imports
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from .models import Problem, Attempt, Hint, UserProgress

logger = logging.getLogger(__name__)

class RAGService:
    """
    Retrieval-Augmented Generation service for enhanced hint generation.
    Uses similar problems and user history to provide more contextual hints.
    """
    
    def __init__(self):
        logger.info("🚀 Initializing RAG Service...")
        
        self.api_key = settings.OPENROUTER_API_KEY
        
        # Initialize LLM for RAG-enhanced hint generation
        self.rag_llm = ChatOpenAI(
            model='deepseek/deepseek-r1-0528-qwen3-8b:free',
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        # Initialize TF-IDF vectorizer for similarity search
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Cache for problem embeddings
        self.problem_embeddings = {}
        self.problem_texts = {}
        
        # Build RAG chains
        self._build_rag_chains()
        
        logger.info("✅ RAG Service initialized successfully")
    
    def _build_rag_chains(self):
        """Build RAG-enhanced hint generation chain"""
        
        # RAG-enhanced hint generation prompt
        self.rag_hint_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Current Code:
        {user_code}
        
        User Progress:
        - Total Attempts: {attempts_count}
        - Failed Attempts: {failed_attempts_count}
        - Current Hint Level: {current_hint_level}
        - Time Since Last Attempt: {time_since_last_attempt} seconds
        
        Previous Hints Given:
        {previous_hints}
        
        Current Hint Level: {hint_level}
        Hint Type: {hint_type}
        
        Similar Problems Context (from user's history):
        {similar_problems_context}
        
        User's Previous Solutions:
        {user_previous_solutions}
        
        Common Error Patterns (from similar problems):
        {error_patterns}
        
        Please generate a hint that:
        1. Is non-revealing (doesn't give away the solution)
        2. Is appropriate for hint level {hint_level} and type {hint_type}
        3. Builds upon previous hints and user's progress
        4. Uses insights from similar problems the user has solved
        5. Addresses common error patterns from similar problems
        6. Is specific to their current code and approach
        7. Provides pedagogical value by encouraging problem-solving skills
        8. Leverages the user's learning history and patterns
        
        The hint should be:
        - More conceptual for early levels
        - More specific for higher levels
        - Focused on the current hint type
        - Aligned with the user's learning progress
        - Enhanced with context from similar problems
        
        Provide only the hint content, no additional formatting.
        """)
        
        self.rag_hint_chain = (
            self.rag_hint_prompt 
            | self.rag_llm 
            | StrOutputParser()
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for similarity search"""
        # Remove code blocks and special characters
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()
    
    def _get_problem_embedding(self, problem: Problem) -> np.ndarray:
        """Get or compute TF-IDF embedding for a problem"""
        if problem.id in self.problem_embeddings:
            return self.problem_embeddings[problem.id]
        
        # Create problem text representation
        problem_text = f"{problem.title} {problem.description} {problem.difficulty}"
        processed_text = self._preprocess_text(problem_text)
        
        # Store for later use
        self.problem_texts[problem.id] = processed_text
        
        # Compute embedding using transform (not fit_transform) to maintain consistent dimensions
        if not hasattr(self, '_vectorizer_fitted'):
            # First time: fit the vectorizer
            embedding = self.vectorizer.fit_transform([processed_text]).toarray()[0]
            self._vectorizer_fitted = True
        else:
            # Subsequent times: transform using existing vocabulary
            embedding = self.vectorizer.transform([processed_text]).toarray()[0]
        
        self.problem_embeddings[problem.id] = embedding
        
        return embedding
    
    def _find_similar_problems(self, current_problem: Problem, user_id: int, k: int = 3) -> List[Problem]:
        """Find similar problems based on content and user history"""
        logger.info(f"🔍 Finding similar problems for problem {current_problem.id} from user {user_id}'s history")
        
        # Get problems that this user has attempted before (excluding current problem)
        user_attempted_problems = Problem.objects.filter(
            attempts__user_id=user_id
        ).exclude(id=current_problem.id).distinct()
        
        if not user_attempted_problems.exists():
            logger.info(f"⚠️  User {user_id} has no previous problem attempts")
            return []
        
        logger.info(f"📊 User {user_id} has attempted {user_attempted_problems.count()} different problems")
        
        # Get current problem embedding
        current_embedding = self._get_problem_embedding(current_problem)
        
        # Compute similarities with user's attempted problems
        similarities = []
        for problem in user_attempted_problems:
            try:
                problem_embedding = self._get_problem_embedding(problem)
                similarity = cosine_similarity([current_embedding], [problem_embedding])[0][0]
                similarities.append((problem, similarity))
                logger.debug(f"   - Similarity with {problem.title}: {similarity:.3f}")
            except Exception as e:
                logger.warning(f"Error computing similarity for problem {problem.id}: {e}")
                continue
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top k similar problems from user's history
        similar_problems = [problem for problem, _ in similarities[:k]]
        
        logger.info(f"✅ Found {len(similar_problems)} similar problems from user {user_id}'s history")
        for i, problem in enumerate(similar_problems, 1):
            similarity_score = similarities[i-1][1]
            logger.info(f"   {i}. {problem.title} (similarity: {similarity_score:.3f})")
        
        return similar_problems
    
    def _get_user_previous_solutions(self, user_id: int, similar_problems: List[Problem]) -> Dict[str, str]:
        """Get user's previous solutions for similar problems"""
        logger.info(f"📚 Getting previous solutions for user {user_id}")
        
        user_solutions = {}
        
        for problem in similar_problems:
            # Get successful attempts by this user for this problem
            successful_attempts = Attempt.objects.filter(
                user_id=user_id,
                problem=problem,
                status='success'
            ).order_by('-created_at')
            
            if successful_attempts.exists():
                latest_attempt = successful_attempts.first()
                user_solutions[problem.title] = latest_attempt.code
        
        logger.info(f"✅ Found {len(user_solutions)} previous solutions")
        return user_solutions
    
    def _get_error_patterns(self, similar_problems: List[Problem], user_id: int) -> List[str]:
        """Extract common error patterns from similar problems (from same user's attempts)"""
        logger.info(f"🔍 Extracting error patterns from user {user_id}'s attempts on similar problems")
        
        error_patterns = []
        
        for problem in similar_problems:
            # Get failed attempts for this problem by the same user
            failed_attempts = Attempt.objects.filter(
                problem=problem,
                user_id=user_id,
                status='failed'
            )[:5]  # Limit to recent failed attempts
            
            logger.debug(f"   - Found {failed_attempts.count()} failed attempts for {problem.title}")
            
            for attempt in failed_attempts:
                if attempt.evaluation_details:
                    try:
                        eval_data = attempt.evaluation_details
                        if isinstance(eval_data, str):
                            eval_data = json.loads(eval_data)
                        
                        reason = eval_data.get('reason', '')
                        if reason:
                            error_patterns.append(reason)
                            logger.debug(f"     - Error pattern: {reason[:100]}...")
                    except Exception as e:
                        logger.warning(f"Error parsing evaluation details: {e}")
                        continue
        
        # Remove duplicates and limit
        unique_patterns = list(set(error_patterns))[:5]
        
        logger.info(f"✅ Found {len(unique_patterns)} unique error patterns from user {user_id}'s history")
        return unique_patterns
    
    def _build_similar_problems_context(self, similar_problems: List[Problem]) -> str:
        """Build context string from similar problems"""
        if not similar_problems:
            return "No similar problems found in user's history."
        
        context_parts = []
        for i, problem in enumerate(similar_problems, 1):
            context_parts.append(f"{i}. {problem.title} ({problem.difficulty}): {problem.description[:200]}...")
        
        return "\n".join(context_parts)
    
    def _build_user_solutions_context(self, user_solutions: Dict[str, str]) -> str:
        """Build context string from user's previous solutions"""
        if not user_solutions:
            return "No previous solutions found for similar problems."
        
        context_parts = []
        for problem_title, code in user_solutions.items():
            # Truncate code for context
            truncated_code = code[:300] + "..." if len(code) > 300 else code
            context_parts.append(f"Problem: {problem_title}\nSolution: {truncated_code}")
        
        return "\n\n".join(context_parts)
    
    def _build_error_patterns_context(self, error_patterns: List[str]) -> str:
        """Build context string from error patterns"""
        if not error_patterns:
            return "No common error patterns identified."
        
        return "Common errors in similar problems:\n" + "\n".join([f"- {pattern}" for pattern in error_patterns])
    
    def generate_rag_enhanced_hint(
        self,
        problem_description: str,
        user_code: str,
        previous_hints: List[Dict],
        hint_level: int,
        user_progress: Dict,
        hint_type: str = 'conceptual',
        user_id: int = None,
        problem_id: int = None
    ) -> str:
        """Generate RAG-enhanced hint using similar problems and user history"""
        
        logger.info("🎯 Generating RAG-enhanced hint...")
        
        try:
            # Get current problem
            if problem_id:
                current_problem = Problem.objects.get(id=problem_id)
            else:
                # Try to find problem by description
                current_problem = Problem.objects.filter(
                    description__icontains=problem_description[:100]
                ).first()
            
            if not current_problem:
                logger.warning("Could not identify current problem, falling back to basic hint generation")
                return self._generate_basic_hint(problem_description, user_code, previous_hints, hint_level, user_progress, hint_type)
            
            # Find similar problems
            similar_problems = self._find_similar_problems(current_problem, user_id or 0)
            
            # Get user's previous solutions
            user_solutions = self._get_user_previous_solutions(user_id or 0, similar_problems)
            
            # Get error patterns from user's attempts
            error_patterns = self._get_error_patterns(similar_problems, user_id)
            
            # Build context strings
            similar_problems_context = self._build_similar_problems_context(similar_problems)
            user_solutions_context = self._build_user_solutions_context(user_solutions)
            error_patterns_context = self._build_error_patterns_context(error_patterns)
            
            # Prepare inputs for RAG chain
            inputs = {
                "problem_description": problem_description,
                "user_code": user_code,
                "attempts_count": user_progress.get('attempts_count', 0),
                "failed_attempts_count": user_progress.get('failed_attempts_count', 0),
                "current_hint_level": user_progress.get('current_hint_level', 1),
                "time_since_last_attempt": user_progress.get('time_since_last_attempt', 0),
                "previous_hints": "\n".join([h if isinstance(h, str) else h.get('content', str(h)) for h in previous_hints]),
                "hint_level": hint_level,
                "hint_type": hint_type,
                "similar_problems_context": similar_problems_context,
                "user_previous_solutions": user_solutions_context,
                "error_patterns": error_patterns_context
            }
            
            # Generate RAG-enhanced hint
            rag_hint = self.rag_hint_chain.invoke(inputs)
            
            logger.info(f"✅ Generated RAG-enhanced hint: {len(rag_hint)} characters")
            return rag_hint
            
        except Exception as e:
            logger.error(f"❌ Error in RAG-enhanced hint generation: {e}")
            # Fallback to basic hint generation
            return self._generate_basic_hint(problem_description, user_code, previous_hints, hint_level, user_progress, hint_type)
    
    def _generate_basic_hint(
        self,
        problem_description: str,
        user_code: str,
        previous_hints: List[Dict],
        hint_level: int,
        user_progress: Dict,
        hint_type: str = 'conceptual'
    ) -> str:
        """Fallback basic hint generation without RAG"""
        logger.info("🔄 Falling back to basic hint generation")
        
        basic_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Current Code:
        {user_code}
        
        Current Hint Level: {hint_level}
        Hint Type: {hint_type}
        
        Generate a helpful hint that guides the user without giving away the solution.
        """)
        
        basic_chain = basic_prompt | self.rag_llm | StrOutputParser()
        
        return basic_chain.invoke({
            "problem_description": problem_description,
            "user_code": user_code,
            "hint_level": hint_level,
            "hint_type": hint_type
        })
    
    def get_user_learning_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze user's learning patterns for personalization"""
        logger.info(f"📊 Analyzing learning patterns for user {user_id}")
        
        # Get user's attempt history
        attempts = Attempt.objects.filter(user_id=user_id).order_by('created_at')
        
        if not attempts.exists():
            return {}
        
        # Analyze patterns
        patterns = {
            'total_attempts': attempts.count(),
            'success_rate': attempts.filter(status='success').count() / attempts.count(),
            'average_attempts_per_problem': {},
            'preferred_hint_levels': {},
            'common_error_types': [],
            'problem_difficulty_preference': {}
        }
        
        # Group by problem
        for attempt in attempts:
            problem_title = attempt.problem.title
            
            if problem_title not in patterns['average_attempts_per_problem']:
                patterns['average_attempts_per_problem'][problem_title] = 0
            patterns['average_attempts_per_problem'][problem_title] += 1
        
        # Calculate averages
        if patterns['average_attempts_per_problem']:
            avg_attempts = sum(patterns['average_attempts_per_problem'].values()) / len(patterns['average_attempts_per_problem'])
            patterns['average_attempts_per_problem'] = avg_attempts
        
        logger.info(f"✅ Analyzed learning patterns for user {user_id}")
        return patterns
    
    def update_problem_embeddings(self):
        """Update problem embeddings cache"""
        logger.info("🔄 Updating problem embeddings cache")
        
        problems = Problem.objects.all()
        
        # Clear existing cache
        self.problem_embeddings.clear()
        self.problem_texts.clear()
        
        # Recompute embeddings
        for problem in problems:
            try:
                self._get_problem_embedding(problem)
            except Exception as e:
                logger.warning(f"Error updating embedding for problem {problem.id}: {e}")
        
        logger.info(f"✅ Updated embeddings for {len(self.problem_embeddings)} problems") 