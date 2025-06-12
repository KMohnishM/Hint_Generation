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

    def _create_attempt(self, user_id, problem, user_code):
        """Create a new attempt record"""
        return Attempt.objects.create(
            user_id=user_id,
            problem=problem,
            code=user_code,
            status='pending'
        )

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
        
        # Calculate time since last attempt
        time_since_last_attempt = 0
        if progress.last_activity:
            time_since_last_attempt = (timezone.now() - progress.last_activity).total_seconds()
        
        progress.last_activity = timezone.now()
        progress.save()

        # Create attempt record
        attempt = self._create_attempt(user_id, problem, user_code)

        # Get previous hints
        previous_hints = self._get_previous_hints(user_id, problem)
        previous_hints_text = [delivery.hint.content for delivery in previous_hints]

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
            hint_level=progress.current_hint_level,
            user_progress=user_progress_data
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

        # Update user progress
        progress.current_hint_level += 1
        progress.save()

        return Response({
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
