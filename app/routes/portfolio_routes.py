from flask import Blueprint, jsonify, request, current_app, g

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.db import db
from app.schemas.portfolio_schemas import CreatePortfolioSchema
from app.auth import required_auth
from app.common.request_schema import PortfolioSecurityRequestData
from app.common.response_schema import ErrorResponse
from app.models.Investment import Investment

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/', methods=['GET'])
@required_auth
def get_all_portfolios():
    current_app.logger.info("Retrieving all portfolios")
    try:
        portfolios = portfolio_service.get_all_portfolios()
        return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200
    except Exception as e:
        current_app.logger.error(f'Failed to retrieve portfolios: {str(e)}')
        raise



@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@required_auth
def get_portfolio(portfolio_id):
    caller_username = g.user['username']
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify({'error': f'Portfolio {portfolio_id} not found'}), 404
    viewers = [security.username for security in portfolio.portfolio_securities if security.username ==  caller_username and security.role == 'viewer']
    authorized_users = viewers + [portfolio.owner]
    if caller_username not in authorized_users:
        return(ErrorResponse(error_message = f'User {caller_username} is not authorized to view this portfolio', request_id = g.request_id)), 403

    return jsonify(portfolio.__to_dict__()), 200

@portfolio_bp.route('/user/<username>', methods=['GET'])
@required_auth
def get_portfolios_by_user(username):
    caller_username = g.user['username']
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': f'User {username} not found'}), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)

    try:
        authorized_portfolios = []
        for portfolio in portfolios:
            viewers = [s.username for s in portfolio.portfolio_securities if s.username == caller_username and s.role == "viewer"]
            authorized_users = viewers + [portfolio.owner]
            if caller_username in authorized_users:
                authorized_portfolios.append(portfolio)
        return jsonify([p.__to_dict__() for p in authorized_portfolios]), 200

    except Exception as e:
        error_msg = f"Failed to authorize access to portfolios for user {username}: {str(e)}"
        current_app.logger.error(error_msg)
        return jsonify(ErrorResponse(error_message=error_msg, request_id=g.request_id).model_dump()), 500


@portfolio_bp.route('/', methods=['POST'])
@required_auth
def create_portfolio():
    req_data = CreatePortfolioSchema(**request.get_json())
    username = g.user["username"]
    user = user_service.get_user_by_username(username)
    if user is None:
        current_app.logger.debug('some error happened at this line...')
        return jsonify({'error': f'User {username} not found'}), 404
        # authorize that user is allowed to perform this action
    portfolio_id = portfolio_service.create_portfolio(
        name=req_data.name,
        description=req_data.description,
        user=user
    )
    db.session.commit()
    return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@required_auth
def delete_portfolio(portfolio_id):
    caller_username = g.user['username']

    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    
    if portfolio is None:
        return jsonify(ErrorResponse(error_message=f'Portfolio with ID {portfolio_id} does not exist', request_id=g.request_id).model_dump()), 404

    if portfolio.owner != caller_username:
        return jsonify(ErrorResponse(error_message=f'Only owners are allowed to delete their portfolios. {caller_username} is not the owner of portfolio with ID {portfolio_id}', request_id=g.request_id).model_dump()), 403

    portfolio_service.delete_portfolio(portfolio_id)
    db.session.commit()

    return jsonify({'message': 'Portfolio deleted successfully'}), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@required_auth
def get_portfolio_transactions(portfolio_id):
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200

@portfolio_bp.route('/<int:portfolio_id>/security', methods = ['POST'])
@required_auth
def add_portfolio_security(portfolio_id):
    create_portfolio_security_req = PortfolioSecurityRequestData(**request.json)
    portfolio_service.create_portfolio_security(portfolio_id = portfolio_id, username = create_portfolio_security_req.username, role = create_portfolio_security_req.role, caller_user=g.user['username'])
    return jsonify('Portfolio security updated successfully'), 200


@portfolio_bp.route("/<int:portfolio_id>/access", methods=["POST"])
@required_auth
def grant_portfolio_access(portfolio_id):
    data = request.get_json() or {}
    target_username = data.get("username")
    role = data.get("role")

    if role not in ("viewer", "manager"):
        return jsonify({"error": "Invalid role"}), 400

    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    caller = g.user["username"]
    if portfolio.owner != caller:
        return jsonify({"error": "Forbidden"}), 403

    portfolio_service.grant_access(portfolio_id, target_username, role)

    return jsonify({"message": "Access granted"}), 200


@portfolio_bp.route("/<int:portfolio_id>/access/<string:username>", methods=["DELETE"])
@required_auth
def revoke_portfolio_access(portfolio_id, username):
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    caller = g.user["username"]
    if portfolio.owner != caller:
        return jsonify({"error": "Forbidden"}), 403

    success = portfolio_service.revoke_access(portfolio_id, username)
    if not success:
        return jsonify({"error": "Access not found"}), 404
    
    db.session.commit()

    return jsonify({"message": "Access revoked"}), 200




@portfolio_bp.route('/<int:portfolio_id>/holdings', methods=['GET'])
@required_auth
def get_portfolio_holdings(portfolio_id):
    investments = Investment.query.filter_by(portfolio_id=portfolio_id).all()
    return jsonify([inv.__to_dict__() for inv in investments])

