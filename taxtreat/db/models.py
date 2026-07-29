from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    iso2 = Column(String, nullable=False, unique=True)
    iso3 = Column(String, unique=True)
    name_en = Column(String, nullable=False)
    name_local = Column(String)


class Treaty(Base):
    __tablename__ = "treaties"

    id = Column(Integer, primary_key=True)
    country_a_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    country_b_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    treaty_type = Column(String, nullable=False, default="DTT")
    signed_date = Column(String)
    effective_from = Column(String)
    effective_to = Column(String)
    status = Column(String, nullable=False, default="active")


class TreatyVersion(Base):
    __tablename__ = "treaty_versions"

    id = Column(Integer, primary_key=True)
    treaty_id = Column(Integer, ForeignKey("treaties.id"), nullable=False)
    language = Column(String, nullable=False)
    source_file = Column(String)
    is_authentic = Column(Integer, nullable=False, default=0)
    valid_from = Column(String)
    valid_to = Column(String)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    treaty_version_id = Column(Integer, ForeignKey("treaty_versions.id"), nullable=False)
    article_number = Column(Integer, nullable=False)
    title = Column(String)


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    paragraph_number = Column(String)
    text = Column(Text, nullable=False)
