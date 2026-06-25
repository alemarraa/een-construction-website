FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the package in editable mode so the CLI is available
RUN pip install --no-cache-dir -e .

VOLUME ["/app/data"]
ENV DATABASE_URL=sqlite:////app/data/outreach.db

ENTRYPOINT ["python", "-m", "een_outreach.cli"]
CMD ["--help"]
