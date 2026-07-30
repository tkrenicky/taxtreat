from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from taxtreat.db.models import (
    Article,
    Base,
    Country,
    Paragraph,
    Treaty,
    TreatyVersion,
)


def test_database_models_create_tables_and_store_records():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "countries",
        "treaties",
        "treaty_versions",
        "articles",
        "paragraphs",
    }

    with Session(engine) as session:
        country_a = Country(
            iso2="CZ",
            iso3="CZE",
            name_en="Czech Republic",
            name_local="Česká republika",
        )
        country_b = Country(
            iso2="CH",
            iso3="CHE",
            name_en="Switzerland",
            name_local="Schweiz",
        )

        session.add_all([country_a, country_b])
        session.flush()

        treaty = Treaty(
            country_a_id=country_a.id,
            country_b_id=country_b.id,
            signed_date="1995-12-04",
            effective_from="1996-01-01",
        )
        session.add(treaty)
        session.flush()

        version = TreatyVersion(
            treaty_id=treaty.id,
            language="en",
            source_file="cz-ch-dtt.pdf",
            is_authentic=1,
            valid_from="1996-01-01",
        )
        session.add(version)
        session.flush()

        article = Article(
            treaty_version_id=version.id,
            article_number=10,
            title="Dividends",
        )
        session.add(article)
        session.flush()

        paragraph = Paragraph(
            article_id=article.id,
            paragraph_number="1",
            text="Dividends paid by a company...",
        )
        session.add(paragraph)
        session.commit()

        stored_country = session.get(Country, country_a.id)
        stored_treaty = session.get(Treaty, treaty.id)
        stored_version = session.get(TreatyVersion, version.id)
        stored_article = session.get(Article, article.id)
        stored_paragraph = session.get(Paragraph, paragraph.id)

        assert stored_country.iso2 == "CZ"
        assert stored_country.iso3 == "CZE"
        assert stored_country.name_en == "Czech Republic"
        assert stored_country.name_local == "Česká republika"

        assert stored_treaty.country_a_id == country_a.id
        assert stored_treaty.country_b_id == country_b.id
        assert stored_treaty.treaty_type == "DTT"
        assert stored_treaty.status == "active"
        assert stored_treaty.effective_to is None

        assert stored_version.language == "en"
        assert stored_version.source_file == "cz-ch-dtt.pdf"
        assert stored_version.is_authentic == 1
        assert stored_version.valid_to is None

        assert stored_article.article_number == 10
        assert stored_article.title == "Dividends"

        assert stored_paragraph.paragraph_number == "1"
        assert stored_paragraph.text == "Dividends paid by a company..."


def test_model_table_names_and_columns():
    assert Country.__tablename__ == "countries"
    assert Treaty.__tablename__ == "treaties"
    assert TreatyVersion.__tablename__ == "treaty_versions"
    assert Article.__tablename__ == "articles"
    assert Paragraph.__tablename__ == "paragraphs"

    assert set(Country.__table__.columns.keys()) == {
        "id",
        "iso2",
        "iso3",
        "name_en",
        "name_local",
    }

    assert set(Treaty.__table__.columns.keys()) == {
        "id",
        "country_a_id",
        "country_b_id",
        "treaty_type",
        "signed_date",
        "effective_from",
        "effective_to",
        "status",
    }

    assert set(TreatyVersion.__table__.columns.keys()) == {
        "id",
        "treaty_id",
        "language",
        "source_file",
        "is_authentic",
        "valid_from",
        "valid_to",
    }

    assert set(Article.__table__.columns.keys()) == {
        "id",
        "treaty_version_id",
        "article_number",
        "title",
    }

    assert set(Paragraph.__table__.columns.keys()) == {
        "id",
        "article_id",
        "paragraph_number",
        "text",
    }
