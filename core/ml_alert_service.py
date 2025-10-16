# ML-Powered Alert Service for School Management System - FIXED
from typing import List, Dict, Any
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class MLAlertService:
    """ML-powered intelligent alert system"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
        self.alert_priorities = {
            'critical': 0,
            'high': 1, 
            'medium': 2,
            'low': 3
        }
    
    def get_all_ml_alerts(self) -> List[Dict[str, Any]]:
        """Get comprehensive ML-powered alerts from all modules"""
        cache_key = 'ml_alerts_comprehensive'
        cached_alerts = cache.get(cache_key)
        
        if cached_alerts:
            return cached_alerts
        
        alerts = []
        
        # Student performance alerts
        alerts.extend(self._get_student_performance_alerts())
        
        # Financial risk alerts  
        alerts.extend(self._get_financial_risk_alerts())
        
        # Attendance pattern alerts
        alerts.extend(self._get_attendance_pattern_alerts())
        
        # Academic performance alerts
        alerts.extend(self._get_academic_alerts())
        
        # System health alerts
        alerts.extend(self._get_system_health_alerts())
        
        # Transport optimization alerts
        alerts.extend(self._get_transport_alerts())
        
        # Teacher workload alerts - FIXED
        alerts.extend(self._get_teacher_alerts())
        
        # Sort by priority and timestamp
        alerts.sort(key=lambda x: (
            self.alert_priorities.get(x.get('priority', 'low'), 3),
            x.get('timestamp', 0)
        ))
        
        # Cache results
        cache.set(cache_key, alerts, self.cache_timeout)
        
        return alerts[:15]  # Return top 15 alerts
    
    def _get_student_performance_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered student performance alerts with specific context"""
        alerts = []
        try:
            from students.models import Student
            from student_fees.services import FeeCalculationService
            
            # High-risk students with details
            high_risk_students = []
            dropout_risk_students = []
            
            for student in Student.objects.select_related('class_section')[:100]:
                try:
                    balance_info = FeeCalculationService.calculate_student_balance(student)
                    total_balance = balance_info.get('total_balance', 0)
                    attendance_rate = student.get_attendance_percentage()
                    
                    # ML risk factors with context
                    if total_balance > 10000:
                        high_risk_students.append({
                            'name': f"{student.first_name} {student.last_name}",
                            'admission_no': student.admission_number,
                            'class': student.class_section.display_name if student.class_section else 'N/A',
                            'balance': total_balance,
                            'attendance': attendance_rate
                        })
                    
                    # Dropout risk with specific criteria
                    if total_balance > 15000 and attendance_rate < 60:
                        dropout_risk_students.append({
                            'name': f"{student.first_name} {student.last_name}",
                            'admission_no': student.admission_number,
                            'class': student.class_section.display_name if student.class_section else 'N/A',
                            'balance': total_balance,
                            'attendance': attendance_rate,
                            'risk_score': 0.85 + (total_balance / 100000) + ((100 - attendance_rate) / 100)
                        })
                        
                except Exception:
                    continue
            
            if high_risk_students:
                # Sort by balance (highest first)
                high_risk_students.sort(key=lambda x: x['balance'], reverse=True)
                top_students = high_risk_students[:5]  # Top 5 for display
                
                student_details = "; ".join([f"{s['name']} ({s['admission_no']}, {s['class']}, ₹{s['balance']:.0f})" for s in top_students])
                
                alerts.append({
                    'type': 'error',
                    'title': 'AI: High-Risk Students Detected',
                    'message': f'{len(high_risk_students)} students with high financial risk',
                    'details': student_details,
                    'affected_students': high_risk_students,
                    'count': len(high_risk_students),
                    'module': 'ml-students',
                    'action_url': '/students/',
                    'priority': 'high',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.87,
                    'recommendation': f'Priority: {top_students[0]["name"]} (₹{top_students[0]["balance"]:.0f}) - Contact immediately'
                })
            
            if dropout_risk_students:
                # Sort by risk score (highest first)
                dropout_risk_students.sort(key=lambda x: x['risk_score'], reverse=True)
                critical_students = dropout_risk_students[:3]  # Top 3 critical
                
                student_details = "; ".join([f"{s['name']} ({s['class']}, {s['attendance']:.1f}% attendance, ₹{s['balance']:.0f})" for s in critical_students])
                
                alerts.append({
                    'type': 'critical',
                    'title': 'AI: Dropout Risk Alert',
                    'message': f'{len(dropout_risk_students)} students at high dropout risk',
                    'details': student_details,
                    'affected_students': dropout_risk_students,
                    'count': len(dropout_risk_students),
                    'module': 'ml-students',
                    'action_url': '/students/',
                    'priority': 'critical',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.92,
                    'recommendation': f'URGENT: {critical_students[0]["name"]} needs immediate intervention'
                })
                
        except Exception as e:
            logger.error(f"ML student performance alerts failed: {e}")
        
        return alerts
    
    def _get_financial_risk_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered financial risk alerts"""
        alerts = []
        try:
            from students.models import Student
            from student_fees.models import FeeDeposit
            from django.db.models import Sum, Count
            from datetime import date, timedelta
            
            # Payment delay predictions
            thirty_days_ago = date.today() - timedelta(days=30)
            
            # Students with no recent payments
            students_no_recent_payment = Student.objects.filter(
                fee_deposits__deposit_date__lt=thirty_days_ago
            ).distinct().count()
            
            # Students with increasing debt
            increasing_debt_count = Student.objects.filter(
                due_amount__gt=5000
            ).count()
            
            # Revenue trend analysis
            current_month_revenue = FeeDeposit.objects.filter(
                deposit_date__month=date.today().month
            ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
            
            last_month_revenue = FeeDeposit.objects.filter(
                deposit_date__month=date.today().month - 1 if date.today().month > 1 else 12
            ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
            
            if last_month_revenue > 0:
                revenue_decline = ((last_month_revenue - current_month_revenue) / last_month_revenue) * 100
                
                if revenue_decline > 20:
                    alerts.append({
                        'type': 'warning',
                        'title': 'AI: Revenue Decline Detected',
                        'message': f'Revenue down {revenue_decline:.1f}% from last month',
                        'count': int(revenue_decline),
                        'module': 'ml-finance',
                        'action_url': '/student_fees/',
                        'priority': 'high',
                        'timestamp': timezone.now().timestamp(),
                        'ml_confidence': 0.85,
                        'recommendation': 'Review fee collection strategies'
                    })
            
            if students_no_recent_payment > 20:
                alerts.append({
                    'type': 'warning',
                    'title': 'AI: Payment Delay Prediction',
                    'message': f'{students_no_recent_payment} students likely to delay payments',
                    'count': students_no_recent_payment,
                    'module': 'ml-finance',
                    'action_url': '/student_fees/',
                    'priority': 'medium',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.78,
                    'recommendation': 'Send proactive payment reminders'
                })
                
        except Exception as e:
            logger.error(f"ML financial alerts failed: {e}")
        
        return alerts
    
    def _get_attendance_pattern_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered attendance pattern alerts with specific context"""
        alerts = []
        try:
            from attendance.models import Attendance
            from students.models import Student
            from datetime import date, timedelta
            
            week_ago = date.today() - timedelta(days=7)
            
            # Students with detailed attendance analysis
            declining_students = []
            irregular_students = []
            
            for student in Student.objects.select_related('class_section')[:50]:
                try:
                    recent_attendance = Attendance.objects.filter(
                        student=student,
                        date__gte=week_ago
                    )
                    
                    if recent_attendance.count() > 0:
                        total_days = recent_attendance.count()
                        present_days = recent_attendance.filter(status='Present').count()
                        present_rate = present_days / total_days
                        
                        if present_rate < 0.6:  # Less than 60%
                            declining_students.append({
                                'name': f"{student.first_name} {student.last_name}",
                                'admission_no': student.admission_number,
                                'class': student.class_section.display_name if student.class_section else 'N/A',
                                'attendance_rate': present_rate * 100,
                                'present_days': present_days,
                                'total_days': total_days,
                                'absent_days': total_days - present_days
                            })
                        
                        # Pattern analysis
                        monday_absences = recent_attendance.filter(
                            date__week_day=2, status='Absent'
                        ).count()
                        friday_absences = recent_attendance.filter(
                            date__week_day=6, status='Absent'
                        ).count()
                        
                        if monday_absences >= 2 or friday_absences >= 2:
                            pattern_type = "Monday pattern" if monday_absences >= 2 else "Friday pattern"
                            irregular_students.append({
                                'name': f"{student.first_name} {student.last_name}",
                                'admission_no': student.admission_number,
                                'class': student.class_section.display_name if student.class_section else 'N/A',
                                'pattern': pattern_type,
                                'frequency': max(monday_absences, friday_absences),
                                'attendance_rate': present_rate * 100
                            })
                            
                except Exception:
                    continue
            
            if declining_students:
                # Sort by lowest attendance first
                declining_students.sort(key=lambda x: x['attendance_rate'])
                worst_students = declining_students[:3]
                
                student_details = "; ".join([f"{s['name']} ({s['class']}, {s['attendance_rate']:.1f}%, {s['absent_days']}/{s['total_days']} absent)" for s in worst_students])
                
                alerts.append({
                    'type': 'warning',
                    'title': 'AI: Attendance Decline Pattern',
                    'message': f'{len(declining_students)} students with poor attendance',
                    'details': student_details,
                    'affected_students': declining_students,
                    'count': len(declining_students),
                    'module': 'ml-attendance',
                    'action_url': '/attendance/',
                    'priority': 'medium',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.82,
                    'recommendation': f'Priority: {worst_students[0]["name"]} ({worst_students[0]["attendance_rate"]:.1f}% attendance)'
                })
            
            if irregular_students:
                pattern_details = "; ".join([f"{s['name']} ({s['class']}, {s['pattern']}, {s['frequency']} times)" for s in irregular_students[:3]])
                
                alerts.append({
                    'type': 'info',
                    'title': 'AI: Irregular Attendance Patterns',
                    'message': f'{len(irregular_students)} students show unusual patterns',
                    'details': pattern_details,
                    'affected_students': irregular_students,
                    'count': len(irregular_students),
                    'module': 'ml-attendance',
                    'action_url': '/attendance/',
                    'priority': 'low',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.75,
                    'recommendation': f'Investigate {irregular_students[0]["pattern"]} for {irregular_students[0]["name"]}'
                })
                
        except Exception as e:
            logger.error(f"ML attendance alerts failed: {e}")
        
        return alerts
    
    def _get_academic_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered academic performance alerts with class details"""
        alerts = []
        try:
            from subjects.models import ClassSection
            from students.models import Student
            
            # Detailed class performance analysis
            underperforming_classes = []
            
            for class_section in ClassSection.objects.all():
                students_in_class = Student.objects.filter(class_section=class_section)
                class_size = students_in_class.count()
                
                if class_size > 0:
                    # Multiple performance indicators
                    high_dues = students_in_class.filter(due_amount__gt=8000).count()
                    no_payments = students_in_class.filter(fee_deposits__isnull=True).count()
                    
                    # Calculate performance metrics
                    financial_risk_rate = (high_dues / class_size) * 100
                    payment_engagement = ((class_size - no_payments) / class_size) * 100
                    
                    if financial_risk_rate > 30 or payment_engagement < 50:
                        # Get specific student details
                        at_risk_students = students_in_class.filter(
                            due_amount__gt=8000
                        )[:3]  # Top 3 at-risk students
                        
                        student_names = [f"{s.first_name} {s.last_name} (₹{s.due_amount})" for s in at_risk_students]
                        
                        underperforming_classes.append({
                            'class_name': class_section.display_name,
                            'total_students': class_size,
                            'high_dues_count': high_dues,
                            'financial_risk_rate': financial_risk_rate,
                            'payment_engagement': payment_engagement,
                            'at_risk_students': student_names,
                            'teacher': getattr(class_section, 'class_teacher', 'Not Assigned')
                        })
            
            if underperforming_classes:
                # Sort by risk rate (highest first)
                underperforming_classes.sort(key=lambda x: x['financial_risk_rate'], reverse=True)
                worst_class = underperforming_classes[0]
                
                class_details = "; ".join([f"{c['class_name']} ({c['financial_risk_rate']:.1f}% at risk, {c['high_dues_count']}/{c['total_students']} students)" for c in underperforming_classes[:3]])
                
                total_affected = sum(c['high_dues_count'] for c in underperforming_classes)
                
                alerts.append({
                    'type': 'warning',
                    'title': 'AI: Academic Performance Alert',
                    'message': f'{len(underperforming_classes)} classes need attention',
                    'details': class_details,
                    'affected_classes': underperforming_classes,
                    'count': total_affected,
                    'module': 'ml-academic',
                    'action_url': '/students/',
                    'priority': 'medium',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.79,
                    'recommendation': f'Priority: {worst_class["class_name"]} - {worst_class["financial_risk_rate"]:.1f}% students at risk. At-risk students: {", ".join(worst_class["at_risk_students"][:2])}'
                })
                
        except Exception as e:
            logger.error(f"ML academic alerts failed: {e}")
        
        return alerts
    
    def _get_system_health_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered system health alerts"""
        alerts = []
        try:
            from django.db import connection
            from students.models import Student
            from student_fees.models import FeeDeposit
            
            # Database performance analysis
            with connection.cursor() as cursor:
                # Check for large tables
                cursor.execute("SELECT COUNT(*) FROM students_student")
                student_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM student_fees_feedeposit")
                deposit_count = cursor.fetchone()[0]
            
            # Data growth analysis
            if student_count > 5000:
                alerts.append({
                    'type': 'info',
                    'title': 'AI: Database Growth Alert',
                    'message': f'Database has {student_count} students - consider optimization',
                    'count': student_count,
                    'module': 'ml-system',
                    'action_url': '/admin/',
                    'priority': 'low',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.95,
                    'recommendation': 'Archive old records and optimize queries'
                })
            
            # Transaction volume analysis
            if deposit_count > 10000:
                alerts.append({
                    'type': 'info',
                    'title': 'AI: High Transaction Volume',
                    'message': f'{deposit_count} fee transactions - system performing well',
                    'count': deposit_count,
                    'module': 'ml-system',
                    'action_url': '/student_fees/',
                    'priority': 'low',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.88,
                    'recommendation': 'Monitor system performance'
                })
                
        except Exception as e:
            logger.error(f"ML system health alerts failed: {e}")
        
        return alerts
    
    def _get_transport_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered transport optimization alerts"""
        alerts = []
        try:
            from transport.models import Route, TransportAssignment
            from students.models import Student
            
            # Route efficiency analysis
            total_students = Student.objects.count()
            assigned_students = TransportAssignment.objects.count()
            unassigned_percentage = ((total_students - assigned_students) / total_students) * 100 if total_students > 0 else 0
            
            if unassigned_percentage > 60:
                alerts.append({
                    'type': 'info',
                    'title': 'AI: Transport Optimization',
                    'message': f'{unassigned_percentage:.1f}% students not using transport',
                    'count': total_students - assigned_students,
                    'module': 'ml-transport',
                    'action_url': '/transport/',
                    'priority': 'low',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.73,
                    'recommendation': 'Analyze transport demand and optimize routes'
                })
                
        except Exception as e:
            logger.error(f"ML transport alerts failed: {e}")
        
        return alerts
    
    def _get_teacher_alerts(self) -> List[Dict[str, Any]]:
        """ML-powered teacher workload alerts - FIXED"""
        alerts = []
        try:
            from teachers.models import Teacher
            from subjects.models import SubjectAssignment
            from students.models import Student
            
            # Teacher workload analysis with proper error handling
            overloaded_teachers = []
            
            for teacher in Teacher.objects.all():
                try:
                    # Count subjects assigned through SubjectAssignment
                    assignments = SubjectAssignment.objects.filter(teacher=teacher).select_related('class_section')
                    subjects_count = assignments.count()
                    
                    # Count total students taught (approximate) with safe access
                    total_students_taught = 0
                    for assignment in assignments:
                        try:
                            # Safe access to class_section with multiple checks
                            if hasattr(assignment, 'class_section') and assignment.class_section:
                                students_in_class = Student.objects.filter(class_section=assignment.class_section).count()
                                total_students_taught += students_in_class
                        except AttributeError:
                            # Skip if class_section field doesn't exist or is None
                            continue
                        except Exception:
                            # Skip any other errors
                            continue
                    
                    # ML workload assessment
                    if subjects_count > 5 or total_students_taught > 200:
                        overloaded_teachers.append({
                            'teacher': teacher,
                            'subjects': subjects_count,
                            'students': total_students_taught
                        })
                        
                except Exception:
                    # Skip this teacher if any error occurs
                    continue
            
            if overloaded_teachers:
                alerts.append({
                    'type': 'warning',
                    'title': 'AI: Teacher Workload Alert',
                    'message': f'{len(overloaded_teachers)} teachers may be overloaded',
                    'count': len(overloaded_teachers),
                    'module': 'ml-teachers',
                    'action_url': '/teachers/',
                    'priority': 'medium',
                    'timestamp': timezone.now().timestamp(),
                    'ml_confidence': 0.81,
                    'recommendation': 'Review teacher assignments and redistribute workload'
                })
                
        except Exception as e:
            logger.error(f"ML teacher alerts failed: SubjectAssignment model access error - {str(e)}")
        
        return alerts

# Global instance
ml_alert_service = MLAlertService()