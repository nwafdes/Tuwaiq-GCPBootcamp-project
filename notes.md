- enable gemeni api in terraform
- assign Cloudrun function SA a permission to invoke gemeni `roles/aiplatform.user`
- add env variables to cloud run function 
    - GOOGLE_GENAI_USE_VERTEXAI=True
    - GOOGLE_CLOUD_PROJECT=<your-project-id>
    - GOOGLE_CLOUD_LOCATION=global

    .