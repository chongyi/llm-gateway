
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, ModelMapping, ModelMappingProvider, ServiceProvider
from app.repositories.sqlalchemy.model_repo import SQLAlchemyModelRepository

# Setup in-memory SQLite for reproduction
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_delete_model_mapping_error(db_session):
    repo = SQLAlchemyModelRepository(db_session)
    
    # 1. Create a provider
    provider = ServiceProvider(
        name="test-provider",
        base_url="http://localhost",
        protocol="openai"
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    
    # 2. Create a model mapping
    model = ModelMapping(requested_model="test-model")
    db_session.add(model)
    await db_session.commit()
    
    # 3. Create a provider mapping linked to the model
    mapping = ModelMappingProvider(
        requested_model="test-model",
        provider_id=provider.id,
        target_model_name="target-model"
    )
    db_session.add(mapping)
    await db_session.commit()
    
    # 4. Try to delete the model mapping
    # This matches the logic in repo.delete_mapping
    success = await repo.delete_mapping("test-model")
    assert success is True
    
    # Verify it is gone
    result = await repo.get_mapping("test-model")
    assert result is None
