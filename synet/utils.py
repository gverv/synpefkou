# utils.py
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.conf import settings

SMS_STATUS = {
    "20": "Το SMS στάλθηκε, το μήνυμα έγινε δεκτό από το σύστημα",
    "40": "Δεν υπάρχουν διαθέσιμα SMS στον λογαριασμό",
    "41": "Λάθος αριθμός (όχι 10 ψηφία ή άγνωστο πρόθεμα)",
    "42": "Άγνωστη χώρα (unknown prefix)",
    "43": "Προσωρινά άγνωστη χώρα (no routing)",
    "44": "Σημάνθηκε ως spam",
    "52": "Αριθμός στην Black List",
    "60": "Το SMS δεν έγινε δεκτό",
}

def send_sms(to, message):
    """
    Στέλνει SMS χρησιμοποιώντας το SMSBOX API.
    Επιστρέφει dict: {'success': True/False, 'results': [...]} 
    όπου κάθε στοιχείο της λίστας results είναι dict με status, status_msg, id, to
    """
    url = 'https://www.smsbox.gr/httpapi/sendsms.php'
    username = getattr(settings, "SMSBOX_USERNAME", "")
    password = getattr(settings, "SMSBOX_PASSWORD", "")

    if not username or not password:
        return {'success': False, 'error': 'Δεν έχει ρυθμιστεί SMSBOX_USERNAME/ PASSWORD στο settings.py'}

    post_fields = {
        'username': username,
        'password': password,
        'to': to,
        'from': 'SMSBOX Django',
        'text': message,
        'encoding': 'UTF8'
    }

    try:
        request = Request(url, urlencode(post_fields).encode())
        response = urlopen(request).read().decode()

        results = []
        success_overall = True

        for line in response.strip().splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            status_code, msg_id, phone = parts[:3]
            status_msg = SMS_STATUS.get(status_code, "Άγνωστο status")
            results.append({
                'status_code': status_code,
                'status_msg': status_msg,
                'id': msg_id,
                'to': phone
            })
            if status_code != "20":
                success_overall = False

        return {'success': success_overall, 'results': results}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# # utils.py
# import os
# from urllib.parse import urlencode
# from urllib.request import Request, urlopen

# from django.conf import settings

# def send_sms(to, message):
#     """
#     Στέλνει SMS χρησιμοποιώντας το SMSBOX API.
#     Επιστρέφει dict: {'success': True} ή {'success': False, 'error': '...'}
#     """
#     url = 'http://www.smsbox.gr/httpapi/sendsms.php'

#     # Στοιχεία από settings.py
#     username = getattr(settings, "SMSBOX_USERNAME", "")
#     password = getattr(settings, "SMSBOX_PASSWORD", "")

#     if not username or not password:
#         return {'success': False, 'error': 'Δεν έχει ρυθμιστεί SMSBOX_USERNAME/ PASSWORD στο settings.py'}

#     post_fields = {
#         'username': username,
#         'password': password,
#         'to': to,
#         'from': 'SMSBOX Django',
#         'text': message,
#         'encoding': 'UTF8'
#     }

#     try:
#         request = Request(url, urlencode(post_fields).encode())
#         response = urlopen(request).read().decode()
#         # Εδώ μπορείς να προσθέσεις έλεγχο περιεχομένου response
#         if "error" in response.lower():
#             return {'success': False, 'error': response}
#         return {'success': True}
#     except Exception as e:
#         return {'success': False, 'error': str(e)}



# from urllib.parse import urlencode
# from urllib.request import Request, urlopen
# from django.conf import settings

# def send_sms(to, text):
#     url = 'http://www.smsbox.gr/httpapi/sendsms.php'
#     post_fields = {
#         'username': settings.SMSBOX_USERNAME,
#         'password': settings.SMSBOX_PASSWORD,
#         'to': to,
#         'from': settings.SMSBOX_SENDER,
#         'text': text,
#         'encoding': 'UTF8'
#     }
#     request = Request(url, urlencode(post_fields).encode())
#     response = urlopen(request).read().decode()
#     return response
