UPLOAD_RESPONSE = {
    "filename": "photo.jpg",
    "path": "/documents/2026.09.07/material_photo/material_photo_orig_68bc1a2f3e4d51.12345678.jpg",
    "ext": "jpg",
    "fileUrl": "https://office.smartremont.kz/documents/2026.09.07/material_photo/material_photo_orig_68bc1a2f3e4d51.12345678.jpg",
}

MODES_RESPONSE = {
    "backend": "minio",
    "publicBaseUrl": "https://office.smartremont.kz",
    "items": [
        {
            "mode": "MATERIAL_PHOTO",
            "description": "Фото материала (оригинал)",
            "pathTemplate": "/documents/{date}/material_photo/material_photo_orig_{uniq}.{ext}",
        },
        {
            "mode": "REQUEST_DOCS",
            "description": "Документы заявки",
            "pathTemplate": "/documents/{date}/request_docs/request_docs_{n}_{uniq}.{ext}",
        },
    ],
    "total": 2,
}

CONFIG_RESPONSE = {
    "backend": "dual",
    "minioConfigured": True,
    "officeProxyConfigured": True,
    "publicBaseUrl": "https://office.smartremont.kz",
    "minioEndpoint": "https://s3.smartremont.kz",
    "minioBucket": "smartremont",
    "minioStrict": False,
}
