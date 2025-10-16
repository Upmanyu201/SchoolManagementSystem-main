# D:\School-Management-System\School-Management-System-main\student_fees\urls.py
from django.urls import path
from .views import (
    FeeDepositListView,
    FeeDepositCreateView, 
    FeeDepositUpdateView,
    FeeDepositDeleteView,
    get_student_fees, 
    submit_deposit, 
    receipt_view,    
    payment_confirmation,
    student_fee_preview,
    bulk_delete_deposits,
    student_detail_card
)
from .api_views import (
    StudentFeesAPIView,
    process_payment_api,
    StudentBalanceAPIView,
    get_student_fees_ajax,
    submit_deposit_ajax
)


app_name = 'student_fees'

urlpatterns = [
    # Main views
    path('', FeeDepositListView.as_view(), name='fee_deposit'),
    path('student_detail_card/<int:student_id>/', student_detail_card, name='student_detail_card'),
    path('student/<int:student_id>/create/', FeeDepositCreateView.as_view(), name='fee_deposit_create'),
    path('deposit/<int:pk>/edit/', FeeDepositUpdateView.as_view(), name='edit_deposit'),
    path('deposit/<int:pk>/delete/', FeeDepositDeleteView.as_view(), name='delete_deposit'),
    path('bulk-delete/', bulk_delete_deposits, name='bulk_delete_deposits'),
    path('receipt/<str:receipt_no>/', receipt_view, name='receipt_view'),
    path('receipt/<str:receipt_no>/', receipt_view, name='receipt'),
    path('payment/<int:student_id>/', payment_confirmation, name='payment_confirmation'),
    path('preview/<int:student_id>/', student_fee_preview, name='student_fee_preview'),
    
    # Modern API endpoints - match JavaScript expectations
    path('api/student-fees/', StudentFeesAPIView.as_view(), name='api_student_fees'),
    path('api/process-payment/', process_payment_api, name='api_process_payment'),
    path('api/balance/<int:student_id>/', StudentBalanceAPIView.as_view(), name='api_student_balance'),
    
    # Legacy AJAX endpoints (for backward compatibility)
    path('ajax/get-student-fees/', get_student_fees, name='get_student_fees'),
    path('submit-deposit/', submit_deposit, name='submit_deposit'),
    

]