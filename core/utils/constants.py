class Errors:
    def generate_error(msg):
        return {"detail": msg}

    # ===========================================================  User related errors
    INVALID_PHONE_NUMBER_PATTERN = generate_error(
        "Invalid Phone Number pattern (regex)"
    )
    INVALID_OTP_PATTERN = generate_error("Invalid otp code pattern (regex)")
    INVALID_OTP_CODE = generate_error("Invalid otp code")
    OTP_BLANK = generate_error("OTP cant be blank")
    OTP_SPAM = generate_error("Please wait for a while to resend and try again")
    # ===========================================================  Gathering related errors
    GATHERING_HELD = generate_error("gathering has been held")
    Full_capacity = generate_error("All seats are occupied")
    USER_BANNED = generate_error(
        "User account is limited to register for the event, please contact support"
    )
    ALREADY_REGISTERED = generate_error(
        "The user has already registered for this event"
    )
    TIME_CANCELLATION = generate_error(
        "You cannot cancel your ticket (to cancel the ticket, it must be more than 2 days before the event). If you need to cancel immediately, contact support."
    )
    ALREADY_ENTERED = generate_error("already entered")
    INVALID_UUID = generate_error("Invalid UUID")
    INVALID_DISCOUNT_CODE = generate_error("Invalid discount code")
    ALREADY_IS_PAID_TRUE = generate_error(
        "Payment has already been made successfully for this object"
    )
    EVENT_IS_FREE = generate_error("This event is free and you cannot pay a fee")

    # ===========================================================  system related errors
    XSS_ATTACK_DETECTION = generate_error(
        "XSS protection activate, dont use html tags in fields"
    )
    PASSWORD_MISMATCHED = generate_error("Password mismatched")
    SMS_PANEL = generate_error(
        "There was an error sending a message from the SMS panel"
    )
