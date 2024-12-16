from django.conf import settings

RP_DEFAULT_FEEDBACK = [
            {
                "id": 9999991,
                "product_id": 1,
                "custom_feedback": "Great job! Your product is amazing.",
                "user_name": "John Doe",
                "user_image": f"{settings.CAREERS_BASE_IMAGES_URL}john_doe.jpg",
                "created": "2022-05-25 12:30:00",
                "is_default": True,
            },
            {
                "id": 9999992,
                "product_id": 1,
                "custom_feedback": "Keep up the good work! Your product is fantastic.",
                "user_name": "Jane Smith",
                "user_image": f"{settings.CAREERS_BASE_IMAGES_URL}jane_smith.jpg",
                "created": "2022-05-24 10:45:00",
                "is_default": True,
            }
        ]