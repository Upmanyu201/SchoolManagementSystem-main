import webbrowser
import urllib.parse

class WhatsAppGroupService:
    """Service for WhatsApp group operations"""
    
    def send_group_message(self, group_link, message):
        """Send message to WhatsApp group via web"""
        try:
            # Extract group ID from invite link
            if 'chat.whatsapp.com' in group_link:
                # Open WhatsApp Web with group
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"{group_link}?text={encoded_message}"
                webbrowser.open(whatsapp_url)
                
                return {
                    'success': True,
                    'message': 'WhatsApp Web opened for group message'
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid WhatsApp group link'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }