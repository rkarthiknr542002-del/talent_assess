from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q, Avg, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Analytics
from .serializers import AnalyticsSerializer, DateRangeSerializer
from tests.models import Test
from results.models import Result
from accounts.models import User
from core.permissions import IsAdmin

@api_view(['GET'])
@permission_classes([IsAdmin])
def analytics_list(request):
    """
    GET: List all analytics records with filters
    """
    queryset = Analytics.objects.all().order_by('-date')
    
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    
    paginator = Paginator(queryset, page_size)
    current_page = paginator.get_page(page)
    
    serializer = AnalyticsSerializer(current_page, many=True)
    
    return Response({
        'success': True,
        'data': {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
            'results': serializer.data
        }
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def analytics_detail(request, pk):
    """
    GET: Retrieve analytics record by ID
    """
    try:
        analytics = Analytics.objects.get(pk=pk)
    except Analytics.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Analytics record not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AnalyticsSerializer(analytics)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def analytics_summary(request):
    """
    Get analytics summary for a date range
    """
    end_date_str = request.query_params.get('end_date')
    start_date_str = request.query_params.get('start_date')
    
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else end_date - timedelta(days=30)
    except ValueError:
        return Response({
            'success': False,
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    analytics = Analytics.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).order_by('date')

    total_tests = sum(a.total_tests_taken for a in analytics)
    total_candidates = sum(a.total_candidates for a in analytics)
    total_pass = sum(a.pass_count for a in analytics)
    total_fail = sum(a.fail_count for a in analytics)

    level_stats = {}
    tech_stats = {}
    
    for a in analytics:
        if hasattr(a, 'level_wise_stats') and a.level_wise_stats:
            for level, stats in a.level_wise_stats.items():
                if level not in level_stats:
                    level_stats[level] = {'total': 0, 'pass': 0}
                level_stats[level]['total'] += stats.get('total', 0)
                level_stats[level]['pass'] += stats.get('pass', 0)
        
        if hasattr(a, 'technology_wise_stats') and a.technology_wise_stats:
            for tech, stats in a.technology_wise_stats.items():
                if tech not in tech_stats:
                    tech_stats[tech] = {'total': 0, 'total_score': 0, 'avg_score': 0}
                tech_stats[tech]['total'] += stats.get('total', 0)
                tech_stats[tech]['total_score'] += stats.get('avg_score', 0) * stats.get('total', 0)
    
    for tech in tech_stats:
        if tech_stats[tech]['total'] > 0:
            tech_stats[tech]['avg_score'] = round(
                tech_stats[tech]['total_score'] / tech_stats[tech]['total'], 2
            )
        del tech_stats[tech]['total_score']

    for level in level_stats:
        if level_stats[level]['total'] > 0:
            level_stats[level]['pass_rate'] = round(
                (level_stats[level]['pass'] / level_stats[level]['total']) * 100, 2
            )
    
    return Response({
        'success': True,
        'data': {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': len(analytics)
            },
            'overall': {
                'total_tests': total_tests,
                'unique_candidates': total_candidates,
                'pass_count': total_pass,
                'fail_count': total_fail,
                'pass_rate': round((total_pass / total_tests * 100) if total_tests > 0 else 0, 2)
            },
            'level_wise': level_stats,
            'technology_wise': tech_stats,
            'daily_data': AnalyticsSerializer(analytics, many=True).data
        }
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def analytics_trends(request):
    """
    Get trend data for charts
    """
    days = int(request.query_params.get('days', 30))
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    analytics = Analytics.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).order_by('date')
    
    dates = []
    tests_taken = []
    candidates = []
    pass_count = []
    pass_rate = []
    
    for a in analytics:
        dates.append(a.date.strftime('%Y-%m-%d'))
        tests_taken.append(a.total_tests_taken)
        candidates.append(a.total_candidates)
        pass_count.append(a.pass_count)
        
        rate = (a.pass_count / a.total_tests_taken * 100) if a.total_tests_taken > 0 else 0
        pass_rate.append(round(rate, 2))
    
    tech_trends = {}
    tech_counts = {}
    
    for a in analytics:
        if hasattr(a, 'technology_wise_stats') and a.technology_wise_stats:
            for tech, stats in a.technology_wise_stats.items():
                if tech not in tech_trends:
                    tech_trends[tech] = []
                    tech_counts[tech] = 0
                
                tech_trends[tech].append({
                    'date': a.date.strftime('%Y-%m-%d'),
                    'avg_score': stats.get('avg_score', 0)
                })
                tech_counts[tech] += 1
    
    top_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_tech_data = {tech: tech_trends[tech] for tech, _ in top_techs}
    
    return Response({
        'success': True,
        'data': {
            'dates': dates,
            'tests_taken': tests_taken,
            'candidates': candidates,
            'pass_count': pass_count,
            'pass_rate': pass_rate,
            'technology_trends': top_tech_data
        }
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboard_stats(request):
    """
    Get dashboard statistics - COMPLETE FIXED VERSION
    """
    try:
        today = date.today()
        today_analytics = Analytics.objects.filter(date=today).first()

        week_start = today - timedelta(days=today.weekday())
        week_analytics = list(Analytics.objects.filter(date__gte=week_start))

        month_start = date(today.year, today.month, 1)
        month_analytics = list(Analytics.objects.filter(date__gte=month_start))

        all_users = list(User.objects.all())
        all_tests = list(Test.objects.all())
        all_results = list(Result.objects.select_related('test', 'candidate').all())
        
        # Create a mapping of test_id to result
        result_by_test = {}
        for r in all_results:
            if hasattr(r, 'test') and r.test:
                test_id = str(r.test._id)
                result_by_test[test_id] = r

        candidates = [u for u in all_users if getattr(u, 'role', '') == 'candidate']
        total_candidates = len(candidates)
        active_candidates = len([u for u in candidates if getattr(u, 'is_active', False)])

        total_tests = len(all_tests)
        completed_tests = len([t for t in all_tests if getattr(t, 'status', '') == 'completed'])
        in_progress_tests = len([t for t in all_tests if getattr(t, 'status', '') == 'in_progress'])
        pending_tests = len([t for t in all_tests if getattr(t, 'status', '') == 'pending'])

        # Get valid results for recent data
        valid_results = [r for r in all_results if hasattr(r, 'evaluated_at') and r.evaluated_at]
        sorted_results = sorted(valid_results, key=lambda x: x.evaluated_at, reverse=True)[:10]
        
        recent_data = []
        for r in sorted_results:
            recent_data.append({
                'test_id': r.test.test_id if hasattr(r.test, 'test_id') else str(r.test._id),
                'candidate_name': r.candidate.name if r.candidate else 'Unknown',
                'candidate_email': r.candidate.email if r.candidate else '',
                'percentage': r.percentage,
                'passed': r.passed,
                'evaluated_at': r.evaluated_at.isoformat() if r.evaluated_at else None
            })

        # Calculate level distribution from test data directly
        level_distribution = {}
        completed_tests_list = [t for t in all_tests if getattr(t, 'status', '') == 'completed']
        
        for test in completed_tests_list:
            level = getattr(test, 'experience_level', 'unknown')
            if level not in level_distribution:
                level_distribution[level] = {'total': 0, 'passed': 0}
            
            level_distribution[level]['total'] += 1

            # ✅ Use test.passed directly if available
            if hasattr(test, 'passed') and test.passed:
                level_distribution[level]['passed'] += 1
            else:
                # Otherwise check for result
                test_id = str(test._id)
                result = result_by_test.get(test_id)
                if result and result.passed:
                    level_distribution[level]['passed'] += 1

        # Calculate pass rates
        for level in level_distribution:
            if level_distribution[level]['total'] > 0:
                pass_count = level_distribution[level]['passed']
                total_count = level_distribution[level]['total']
                level_distribution[level]['pass_rate'] = round(
                    (pass_count / total_count) * 100, 2
                )

        week_tests_taken = sum(getattr(a, 'total_tests_taken', 0) for a in week_analytics)
        week_pass_count = sum(getattr(a, 'pass_count', 0) for a in week_analytics)

        month_tests_taken = sum(getattr(a, 'total_tests_taken', 0) for a in month_analytics)
        month_pass_count = sum(getattr(a, 'pass_count', 0) for a in month_analytics)
        
        return Response({
            'success': True,
            'data': {
                'today': {
                    'tests_taken': today_analytics.total_tests_taken if today_analytics else 0,
                    'candidates': today_analytics.total_candidates if today_analytics else 0,
                    'pass_count': today_analytics.pass_count if today_analytics else 0,
                    'fail_count': today_analytics.fail_count if today_analytics else 0
                },
                'week': {
                    'tests_taken': week_tests_taken,
                    'candidates': 0,  
                    'pass_count': week_pass_count
                },
                'month': {
                    'tests_taken': month_tests_taken,
                    'candidates': 0, 
                    'pass_count': month_pass_count
                },
                'overall': {
                    'total_tests': total_tests,
                    'completed_tests': completed_tests,
                    'in_progress_tests': in_progress_tests,
                    'pending_tests': pending_tests,
                    'total_candidates': total_candidates,
                    'active_candidates': active_candidates,
                    'inactive_candidates': total_candidates - active_candidates
                },
                'level_distribution': level_distribution,
                'recent_results': recent_data
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdmin])
def generate_analytics(request):
    """
    Generate analytics for a date range - FIXED WITH _id
    """
    from django.utils import timezone
    from datetime import datetime, timedelta, date
    
    serializer = DateRangeSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        end_date = data.get('end_date', date.today())
        start_date = data.get('start_date', end_date)
        
        if start_date > end_date:
            return Response({
                'success': False,
                'message': 'start_date cannot be after end_date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        generated_count = 0
        current_date = start_date
        
        all_tests = list(Test.objects.all())
        all_results = list(Result.objects.all())

        result_by_test = {}
        for r in all_results:
            if hasattr(r, 'test') and r.test:
                result_by_test[str(r.test._id)] = r

        tz = timezone.get_current_timezone()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_start = timezone.make_aware(day_start, tz)
            
            day_end = datetime.combine(current_date, datetime.max.time())
            day_end = timezone.make_aware(day_end, tz)
            
            day_tests = []
            for test in all_tests:
                if not hasattr(test, 'end_time') or not test.end_time:
                    continue
                
                end_time = test.end_time
                if timezone.is_naive(end_time):
                    end_time = timezone.make_aware(end_time, tz)
                
                if day_start <= end_time <= day_end:
                    if getattr(test, 'status', '') == 'completed':
                        day_tests.append(test)
            
            if day_tests:
                total_tests = len(day_tests)
                
                candidates = set()
                for test in day_tests:
                    if hasattr(test, 'candidate') and test.candidate:
                        candidates.add(str(test.candidate._id))  
        
                total_candidates = len(candidates)

                pass_count = 0
                fail_count = 0
                
                for test in day_tests:
                    result = result_by_test.get(str(test._id))
                    if result and hasattr(result, 'passed'):
                        if result.passed:
                            pass_count += 1
                        else:
                            fail_count += 1

                level_stats = {}
                for test in day_tests:
                    level = getattr(test, 'experience_level', 'unknown')
                    if level not in level_stats:
                        level_stats[level] = {'total': 0, 'pass': 0}
                    
                    level_stats[level]['total'] += 1
                    
                    result = result_by_test.get(str(test._id))
                    if result and hasattr(result, 'passed') and result.passed:
                        level_stats[level]['pass'] += 1
                
                tech_stats = {}
                for test in day_tests:
                    result = result_by_test.get(str(test._id))
                    if result and hasattr(result, 'technology_wise') and result.technology_wise:
                        for tech, stats in result.technology_wise.items():
                            if tech not in tech_stats:
                                tech_stats[tech] = {'total': 0, 'total_score': 0, 'avg_score': 0}
                            
                            tech_stats[tech]['total'] += stats.get('total', 0)
                            
                            if stats.get('total', 0) > 0:
                                score_pct = (stats.get('correct', 0) / stats.get('total', 1)) * 100
                                tech_stats[tech]['total_score'] += score_pct
                
                for tech in tech_stats:
                    if tech_stats[tech]['total'] > 0:
                        tech_stats[tech]['avg_score'] = round(
                            tech_stats[tech]['total_score'] / tech_stats[tech]['total'], 2
                        )
                    if 'total_score' in tech_stats[tech]:
                        del tech_stats[tech]['total_score']
                try:
                    Analytics.objects.update_or_create(
                        date=current_date,
                        defaults={
                            'total_tests_taken': total_tests,
                            'total_candidates': total_candidates,
                            'pass_count': pass_count,
                            'fail_count': fail_count,
                            'level_wise_stats': level_stats,
                            'technology_wise_stats': tech_stats
                        }
                    )
                    generated_count += 1
                except Exception as e:
                    print(f"Error saving analytics for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        return Response({
            'success': True,
            'message': f'Analytics generated for {generated_count} days from {start_date} to {end_date}'
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdmin])
def analytics_export(request):
    """
    Export analytics data
    GET /api/analytics/export/?format=csv&start_date=2024-01-01&end_date=2024-01-31
    """
    format_type = request.query_params.get('format', 'json')
    
    queryset = Analytics.objects.all().order_by('-date')
    
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    data = []
    for a in queryset:
        data.append({
            'date': a.date.isoformat(),
            'total_tests_taken': a.total_tests_taken,
            'total_candidates': a.total_candidates,
            'pass_count': a.pass_count,
            'fail_count': a.fail_count,
            'pass_rate': round((a.pass_count / a.total_tests_taken * 100) if a.total_tests_taken > 0 else 0, 2),
            'level_stats': a.level_wise_stats,
            'tech_stats': a.technology_wise_stats
        })
    
    if format_type == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        if data:
            flat_data = []
            for item in data:
                flat_item = {
                    'date': item['date'],
                    'total_tests_taken': item['total_tests_taken'],
                    'total_candidates': item['total_candidates'],
                    'pass_count': item['pass_count'],
                    'fail_count': item['fail_count'],
                    'pass_rate': item['pass_rate'],
                }
                flat_data.append(flat_item)
            
            writer = csv.DictWriter(response, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)
        
        return response
    
    return Response({
        'success': True,
        'data': data
    })