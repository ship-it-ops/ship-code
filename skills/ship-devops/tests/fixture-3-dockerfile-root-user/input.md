# Synthetic Input for Fixture 3: Dockerfile running as root

You are reviewing the following file. Apply the `ship-devops` rubric.

## File: `services/api/Dockerfile`

```dockerfile
FROM python:3.12

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]
```

---

Apply the ship-devops rubric and produce a structured review.
