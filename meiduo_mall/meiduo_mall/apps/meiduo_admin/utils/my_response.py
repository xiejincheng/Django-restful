def my_jwt_response_payload_handler(token, user, request):
    return {
        "token":token,
        "username":user.username,
        "id":user.id
    }