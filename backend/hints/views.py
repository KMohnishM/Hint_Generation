from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Problem, Hint, Attempt, HintDelivery, HintEvaluation, UserProgress
from .services import OpenRouterService

class HintViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.openrouter_service = OpenRouterService()

    def _get_or_create_problem(self, problem_id, problem_data=None):
        """Get existing problem or create new one if needed"""
<<<<<<< Updated upstream
        try:
            # First try to get existing problem
            problem = Problem.objects.get(id=problem_id)
            return problem
        except Problem.DoesNotExist:
            # If problem doesn't exist and we have problem data, create it
            if problem_data:
                problem = Problem.objects.create(
                    title=problem_data.get('title', 'Untitled Problem'),
                    description=problem_data.get('description', ''),
                    difficulty='medium'  # Set a default difficulty
                )
                return problem
            return None
=======
        logger.info(f"🔍 Looking up problem with ID: {problem_id}")
        
        # First try to get existing problem by user-provided problem_id
        try:
            problem = Problem.objects.get(problem_id=problem_id)
            logger.info(f"✅ Found existing problem by problem_id: {problem.title}")
            return problem
        except Problem.DoesNotExist:
            logger.info(f"❌ Problem {problem_id} not found by problem_id")
        
        # If problem doesn't exist and we have problem data, create it
        if problem_data:
            logger.info("📝 Creating new problem from provided data")
            problem = Problem.objects.create(
                problem_id=problem_id,  # Store the user-provided problem_id
                title=problem_data.get('title', 'Untitled Problem'),
                description=problem_data.get('description', ''),
                difficulty='medium'  # Set a default difficulty
            )
            logger.info(f"✅ Created new problem: {problem.title} (problem_id: {problem.problem_id}, db_id: {problem.id})")
            return problem
        
        logger.warning("⚠️  No problem data provided and problem not found")
        return None
>>>>>>> Stashed changes

    def _get_user_progress(self, user_id, problem):
        """Get or create user progress"""
        try:
            progress = UserProgress.objects.get(
                user_id=user_id,
                problem=problem
            )
        except UserProgress.DoesNotExist:
            progress = UserProgress.objects.create(
                user_id=user_id,
                problem=problem,
                attempts_count=0,
                failed_attempts_count=0,
                current_hint_level=1
            )
        return progress

    def _get_previous_hints(self, user_id, problem):
        """Get previous hints for this user and problem"""
        return HintDelivery.objects.filter(
            user_id=user_id,
            hint__problem=problem
        ).select_related('hint').order_by('-created_at')

    def _get_previous_attempts(self, user_id, problem):
        """Get previous attempts for this user and problem"""
        return Attempt.objects.filter(
            user_id=user_id,
            problem=problem
        ).order_by('-created_at')

    def _get_next_hint_level(self, progress: UserProgress, attempt_evaluation: dict) -> int:
        """
        Determine the next hint level based on user progress and attempt evaluation.
        Hint levels:
        1. Conceptual (Basic understanding)
        2. Approach (Problem-solving strategy)
        3. Implementation (Code structure)
        4. Debug (Specific issues)
        5. Solution (Almost complete solution)
        """
        current_level = progress.current_hint_level
        
        # If user has made multiple failed attempts, increase hint level
        if progress.failed_attempts_count >= 3:
            return min(current_level + 1, 5)
            
        # If user is stuck (inactive for 5+ minutes), increase hint level
        if progress.is_stuck():
            return min(current_level + 1, 5)
            
        # If attempt evaluation shows specific issues, adjust level accordingly
        if attempt_evaluation.get('edge_cases'):
            # If missing edge cases, focus on implementation level
            return max(3, current_level)
            
        # If code has complexity issues, focus on approach level
        if 'complexity' in attempt_evaluation.get('reason', '').lower():
            return max(2, current_level)
            
        # If basic logic issues, focus on conceptual level
        if 'logic' in attempt_evaluation.get('reason', '').lower():
            return max(1, current_level)
            
        # Default: stay at current level
        return current_level

    def _get_hint_type(self, hint_level: int, attempt_evaluation: dict) -> str:
        """
        Determine the hint type based on hint level and attempt evaluation.
        Hint types:
        - conceptual: Basic understanding (level 1)
        - approach: Problem-solving strategy (level 2)
        - implementation: Code structure (level 3)
        - debug: Specific issues (level 4)
        """
        # If there are specific issues in the code, use debug type
        if attempt_evaluation.get('edge_cases') or 'error' in attempt_evaluation.get('reason', '').lower():
            return 'debug'
            
        # If there are complexity issues, use approach type
        if 'complexity' in attempt_evaluation.get('reason', '').lower():
            return 'approach'
            
        # Map hint levels to types
        hint_type_map = {
            1: 'conceptual',
            2: 'approach',
            3: 'implementation',
            4: 'debug',
            5: 'debug'  # Level 5 is also debug as it's for specific issues
        }
        
        return hint_type_map.get(hint_level, 'conceptual')

    @action(detail=False, methods=['post'])
    def request_hint(self, request):
        """Request a hint for a problem"""
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        user_code = request.data.get('user_code')
        problem_data = request.data.get('problem_data')

        if not all([user_id, problem_id, user_code]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create problem
        problem = self._get_or_create_problem(problem_id, problem_data)
        if not problem:
            return Response(
                {'error': 'Problem not found and no problem data provided'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create user progress
        progress = self._get_user_progress(user_id, problem)
        
        # Increment attempts count
        progress.attempts_count += 1
        
        # Evaluate the attempt using LLM
        attempt_evaluation = self.openrouter_service.evaluate_attempt(
            problem_description=problem.description,
            user_code=user_code
        )
        
        # Update failed attempts count if attempt was unsuccessful
        if not attempt_evaluation['success']:
            progress.failed_attempts_count += 1
        
        # Calculate time since last attempt
        time_since_last_attempt = 0
        if progress.last_activity:
            time_since_last_attempt = (timezone.now() - progress.last_activity).total_seconds()
        
        progress.last_activity = timezone.now()
        progress.save()

<<<<<<< Updated upstream
        # Create attempt record with evaluation details
=======
        # Escalate hint level if user is inactive for 5+ minutes
        if time_since_last_attempt > 300:
            logger.info("⏫ User inactive for 5+ minutes, escalating hint level")
            progress.current_hint_level = min(progress.current_hint_level + 1, 5)
            progress.save()

        # Get previous hints (last 5)
        previous_hints = list(self._get_previous_hints(user_id, problem)[:5])
        previous_hints_text = [hint.hint.content for hint in previous_hints]

        # Prepare input for the chain
        chain_input = {
            "problem_description": problem.description,
            "user_code": user_code,
            "attempts_count": progress.attempts_count,
            "failed_attempts_count": progress.failed_attempts_count,
            "current_hint_level": progress.current_hint_level,
            "time_since_last_attempt": time_since_last_attempt,
            "previous_hints": previous_hints_text,
            "hint_level": progress.current_hint_level,
            "hint_type": "conceptual",
            "user_id": user_id,
            "problem_id": problem.id
        }

        # Run the full workflow chain
        logger.info("🔄 Running HintChain workflow...")
        result = self.hint_chain.process_hint_request(chain_input)

        # Get updated hint level and type from the chain result
        new_hint_level = result.get('updated_hint_level', progress.current_hint_level)
        new_hint_type = result.get('updated_hint_type', 'conceptual')

        # Check for duplicate hint (avoid delivering same hint as last time)
        if previous_hints_text and result['generated_hint'].strip() == previous_hints_text[0].strip():
            logger.warning("⚠️  Generated hint is a duplicate of the last delivered hint. Regenerating once...")
            # Try regenerating once
            result = self.hint_chain.process_hint_request(chain_input)
            if result['generated_hint'].strip() == previous_hints_text[0].strip():
                logger.warning("⚠️  Still duplicate after regeneration. Delivering as is.")

        # Update user progress with new hint level
        if new_hint_level != progress.current_hint_level:
            logger.info(f"📈 Updating hint level: {progress.current_hint_level} → {new_hint_level}")
            progress.current_hint_level = new_hint_level
            progress.save()

        # Create attempt record
>>>>>>> Stashed changes
        attempt = Attempt.objects.create(
            user_id=user_id,
            problem=problem,
            code=user_code,
            status='failed' if not attempt_evaluation['success'] else 'success',
            evaluation_details=attempt_evaluation
        )

        # If the attempt was successful, return success response without generating a hint
        if attempt_evaluation['success']:
            return Response({
                'status': 'success',
                'message': 'Your solution is correct!',
                'attempt_evaluation': attempt_evaluation,
                'user_progress': {
                    'attempts_count': progress.attempts_count,
                    'failed_attempts_count': progress.failed_attempts_count,
                    'current_hint_level': progress.current_hint_level,
                    'is_stuck': progress.is_stuck(),
                    'time_since_last_attempt': time_since_last_attempt
                }
            })

        # If attempt was unsuccessful, proceed with hint generation
        # Get previous hints
        previous_hints = self._get_previous_hints(user_id, problem)
        previous_hints_text = [delivery.hint.content for delivery in previous_hints]

        # Determine next hint level
        next_hint_level = self._get_next_hint_level(progress, attempt_evaluation)
        progress.current_hint_level = next_hint_level
        progress.save()

        # Determine hint type
        hint_type = self._get_hint_type(next_hint_level, attempt_evaluation)

        # Prepare user progress data
        user_progress_data = {
            'attempts_count': progress.attempts_count,
            'failed_attempts_count': progress.failed_attempts_count,
            'current_hint_level': progress.current_hint_level,
            'is_stuck': progress.is_stuck(),
            'time_since_last_attempt': time_since_last_attempt
        }

        # Generate hint
        hint_content = self.openrouter_service.generate_hint(
            problem_description=problem.description,
            user_code=user_code,
            previous_hints=previous_hints_text,
            hint_level=next_hint_level,
            user_progress=user_progress_data,
            hint_type=hint_type  # Pass hint type to the generator
        )

        # Create hint
        hint = Hint.objects.create(
            problem=problem,
            content=hint_content,
            level=next_hint_level,
            hint_type=hint_type  # Set the hint type
        )

        # Create hint delivery
        HintDelivery.objects.create(
            hint=hint,
            user_id=user_id,
            attempt=attempt
        )

        # Evaluate hint
        evaluation = self.openrouter_service.evaluate_hint(
            hint_content=hint_content,
            problem_description=problem.description,
            user_code=user_code,
            user_progress=user_progress_data,
            previous_hints=previous_hints_text
        )

        # Create evaluation record
        HintEvaluation.objects.create(
            hint=hint,
            safety_score=evaluation['safety_score'],
            helpfulness_score=evaluation['helpfulness_score'],
            quality_score=evaluation['quality_score'],
            progress_alignment_score=evaluation['progress_alignment_score'],
            pedagogical_value_score=evaluation['pedagogical_value_score']
        )

        return Response({
            'status': 'failed',
            'hint': {
                'id': hint.id,
                'content': hint.content,
                'level': hint.level,
                'type': hint.hint_type
            },
            'evaluation': {
                'safety_score': evaluation['safety_score'],
                'helpfulness_score': evaluation['helpfulness_score'],
                'quality_score': evaluation['quality_score'],
                'progress_alignment_score': evaluation['progress_alignment_score'],
                'pedagogical_value_score': evaluation['pedagogical_value_score']
            },
            'attempt_id': attempt.id,
            'attempt_evaluation': attempt_evaluation,
            'user_progress': user_progress_data
        })

    @action(detail=False, methods=['post'])
    def check_auto_trigger(self, request):
        """Check if a hint should be auto-triggered"""
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        user_code = request.data.get('user_code')
        problem_data = request.data.get('problem_data')

        if not all([user_id, problem_id, user_code]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create problem
        problem = self._get_or_create_problem(problem_id, problem_data)
        if not problem:
            return Response(
                {'error': 'Problem not found and no problem data provided'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user progress
        progress = self._get_user_progress(user_id, problem)
        
        # Check if user is stuck
        if progress.is_stuck():
            # Create attempt record
            attempt = self._create_attempt(user_id, problem, user_code)
            
            # Get previous hints
            previous_hints = self._get_previous_hints(user_id, problem)
            previous_hints_text = [delivery.hint.content for delivery in previous_hints]

            # Generate hint
            hint_content = self.openrouter_service.generate_hint(
                problem_description=problem.description,
                user_code=user_code,
                previous_hints=previous_hints_text,
                hint_level=progress.current_hint_level
            )

            # Create hint
            hint = Hint.objects.create(
                problem=problem,
                content=hint_content,
                level=progress.current_hint_level
            )

            # Create hint delivery
            HintDelivery.objects.create(
                hint=hint,
                user_id=user_id,
                attempt=attempt,
                is_auto_triggered=True
            )

            # Evaluate hint
            evaluation = self.openrouter_service.evaluate_hint(
                hint_content=hint_content,
                problem_description=problem.description,
                user_code=user_code
            )

            # Create evaluation record
            HintEvaluation.objects.create(
                hint=hint,
                safety_score=evaluation['safety_score'],
                helpfulness_score=evaluation['helpfulness_score'],
                quality_score=evaluation['quality_score'],
                progress_alignment_score=evaluation['progress_alignment_score'],
                pedagogical_value_score=evaluation['pedagogical_value_score']
            )

            # Update user progress
            progress.current_hint_level += 1
            progress.save()

            return Response({
                'should_trigger': True,
                'hint': {
                    'id': hint.id,
                    'content': hint.content,
                    'level': hint.level,
                    'type': hint.hint_type
                },
                'evaluation': {
                    'safety_score': evaluation['safety_score'],
                    'helpfulness_score': evaluation['helpfulness_score'],
                    'quality_score': evaluation['quality_score'],
                    'progress_alignment_score': evaluation['progress_alignment_score'],
                    'pedagogical_value_score': evaluation['pedagogical_value_score']
                },
                'attempt_id': attempt.id,
                'user_progress': {
                    'attempts_count': progress.attempts_count,
                    'failed_attempts_count': progress.failed_attempts_count,
                    'current_hint_level': progress.current_hint_level,
                    'is_stuck': progress.is_stuck()
                }
            })

        return Response({
            'should_trigger': False,
            'user_progress': {
                'attempts_count': progress.attempts_count,
                'failed_attempts_count': progress.failed_attempts_count,
                'current_hint_level': progress.current_hint_level,
                'is_stuck': progress.is_stuck()
            }
        })

    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """Provide feedback on a hint delivery"""
        try:
            delivery = HintDelivery.objects.get(id=pk)
        except HintDelivery.DoesNotExist:
            return Response(
                {"error": "Hint delivery not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        feedback = request.data.get('feedback')
        rating = request.data.get('rating')

        if feedback:
            delivery.feedback = feedback
        if rating is not None:
            delivery.rating = rating
        
        delivery.save()

        return Response({
            'status': 'Feedback recorded successfully',
            'hint_id': delivery.hint.id,
            'attempt_id': delivery.attempt.id if delivery.attempt else None
        })
