from setuptools import setup, find_packages

setup(
    name="chatgpt-middleware",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "python-dotenv",
        "pydantic",
        "sqlalchemy",
    ],
    author="angrysky56",
    description="A FastAPI middleware for ChatGPT Custom GPT with CLI, filesystem, and database capabilities",
    keywords="chatgpt, middleware, fastapi, api",
    python_requires=">=3.8",
)
