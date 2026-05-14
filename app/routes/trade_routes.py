from flask import Blueprint, jsonify, request, g

from app.db import db
from app.service import trade_service, portfolio_service
from app.schemas.trade_schemas import ExecuteBuySchema, ExecuteSellSchema
from app.common.response_schema import ErrorResponse
from app.auth import required_auth
from app.service.trade_service import TradeExecutionException

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@required_auth
def execute_purchase_order():

    req_data = ExecuteBuySchema(**request.get_json())
    portfolio_id = req_data.portfolio_id
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error_message = f'Portfolio with ID {portfolio_id} does not exist', request_id = g.request_id).model_dump()), 500
    managers = [security.username for security in portfolio.portfolio_securities if security.role == 'manager']
    authorized_users = managers + [portfolio.owner]
    current_caller = g.user['username']
    if current_caller not in authorized_users:
        return jsonify(ErrorResponse(error_message = f'User {current_caller} is not authorized to perform this activity on portfolio with ID {portfolio_id}', request_id = g.request_id).model_dump()), 403
    trade_service.execute_purchase_order(
        portfolio_id=portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201



@trade_bp.route('/sell', methods=['POST'])
@required_auth
def liquidate_investment():
    req_data = ExecuteSellSchema(**request.get_json())
    portfolio_id = req_data.portfolio_id
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify(ErrorResponse(error_message = f'Portfolio with ID {portfolio_id} does not exist', request_id = g.request_id).model_dump()), 500
    managers = [security.username for security in portfolio.portfolio_securities if security.role == 'manager']
    authorized_users = managers + [portfolio.owner]
    current_caller = g.user['username']
    if current_caller not in authorized_users:
        return jsonify(ErrorResponse(error_message = f'User {current_caller} is not authorized to perform this activity on portfolio with ID {portfolio_id}', request_id = g.request_id).model_dump()), 403
    trade_service.liquidate_investment(
        portfolio_id=req_data.portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity,
        sale_price=req_data.sale_price
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
