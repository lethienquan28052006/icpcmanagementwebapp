from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# This is the base class for all models
class Contest(Base):    
    """
    ORM model for a programming contest.

    Attributes:
        id (int): Primary key, unique contest ID.
        name (str): Name of the contest.
        type (str): Type of the contest (e.g., ICPC, CF).
        phase (str): Current phase of the contest.
        durationSeconds (int): Duration of the contest in seconds.
        standings (list[Standing]): List of standings for this contest.
        problems (list[Problem]): List of problems for this contest.
    """
    __tablename__ = "contests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    phase = Column(String)
    durationSeconds = Column(Integer)

    # Relationship to standings
    standings = relationship("Standing", back_populates="contest", cascade="all, delete-orphan")

    # Relationship to problems
    problems = relationship("Problem", back_populates="contest", cascade="all, delete-orphan")

class Solver(Base):
    """
    ORM model for a solver (participant).

    Attributes:
        id (int): Primary key, unique solver ID.
        handle (str): Unique handle/username of the solver.
        solved_count (int): Total number of problems solved by the solver.
    """
    __tablename__ = "solvers"
    id = Column(Integer, primary_key=True, index=True)
    handle = Column(String, unique=True, nullable=False)
    solved_count = Column(Integer, default=0)

class Problem(Base):
    """
    ORM model for a problem in a contest.

    Attributes:
        id (int): Primary key, unique problem ID.
        name (str): Name of the problem.
        topics (str): Topics/tags associated with the problem.
        contest_id (int): Foreign key to the contest this problem belongs to.
        contest (Contest): Relationship to the Contest model.
    """
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    topics = Column(String, nullable=True)  # Use 'topics' instead of 'tags'
    contest_id = Column(Integer, ForeignKey("contests.id"))

    # Relationship to contest
    contest = relationship("Contest", back_populates="problems")

class Standing(Base):
    """
    ORM model for a contest standing (result for a solver in a contest).

    Attributes:
        id (int): Primary key, unique standing ID.
        handle (str): Handle/username of the solver.
        rank (int): Rank achieved by the solver in the contest.
        problems_solved (int): Number of problems solved by the solver in the contest.
        contest_id (int): Foreign key to the contest.
        contest (Contest): Relationship to the Contest model.
    """
    __tablename__ = "standings"
    id = Column(Integer, primary_key=True, index=True)
    handle = Column(String, nullable=False)
    rank = Column(Integer, nullable=True)
    problems_solved = Column(Integer, nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"))

    # Relationship to contest
    contest = relationship("Contest", back_populates="standings")