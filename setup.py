from setuptools import setup, find_packages

setup(
    name="cookvid",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.39.0",
        "openai-whisper>=20231117",
        "moviepy>=1.0.3",
        "click>=8.1.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.32.0",
        "python-multipart>=0.0.9",
        "jinja2>=3.1.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cookvid=app.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
