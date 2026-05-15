from typing import TYPE_CHECKING

from app.db import db
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models import User, Portfolio

class PortfolioSecurity(db.Model):
    __tablename__ = 'portfoliosecurity'
    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement = True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'), nullable = False)
    username: Mapped[str] = mapped_column(String(30), ForeignKey('user.username'), nullable = False)
    role: Mapped[str] = mapped_column(String(30), nullable = False) # possible values: Viewer and Manager

    user: Mapped['User'] = relationship('User', foreign_keys= [username], lazy = 'selectin')
    portfolio: Mapped['Portfolio'] = relationship('Portfolio', back_populates = 'portfolio_securities', foreign_keys = [portfolio_id], lazy = 'selectin')

# This is used for when we need to create a copy of the object somewhere else in the code
    if TYPE_CHECKING:
        def __init__(self, *, portfolio_id: int, username: str, role: str) -> None: ...
    
    def __str__(self)-> str:
        return f'PortfolioSecurity(id={self.id}, portfolio_id={self.portfolio_id}, username={self.username}, role={self.role})'
    
    def __to_dict__(self):
        return {'id': self.id, 'portfolio_id': self.portfolio_id, 'username': self.username, 'role': self.role}
