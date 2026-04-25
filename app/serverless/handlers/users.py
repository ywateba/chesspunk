import uuid
from serverless.dynamodb import get_table
from serverless.logger import logger

def create_user(body: dict):
    email = body.get('email')
    if not email:
        logger.error("User creation failed: Missing email")
        raise ValueError("Missing email parameter")
        
    user_id = str(uuid.uuid4())
    logger.info(f"Creating new user: {user_id} with email {email}")
    table = get_table('Users')
    
    item = {
        'id': user_id,
        'email': email,
        'role': body.get('role', 'player'),
        'elo': body.get('elo', 1200)
    }
    table.put_item(Item=item)
    return item

def get_user(user_id: str):
    logger.debug(f"Fetching user: {user_id}")
    table = get_table('Users')
    response = table.get_item(Key={'id': user_id})
    return response.get('Item')

def list_users():
    logger.debug("Scanning all users")
    table = get_table('Users')
    return table.scan().get('Items', [])

def update_user(user_id: str, body: dict):
    logger.info(f"Updating user: {user_id}")
    table = get_table('Users')
    
    update_expr = []
    expr_names = {}
    expr_attrs = {}
    
    if 'email' in body:
        update_expr.append("#email = :email")
        expr_names["#email"] = "email"
        expr_attrs[":email"] = body['email']
        
    if 'elo' in body:
        update_expr.append("elo = :elo")
        expr_attrs[":elo"] = body['elo']
        
    if not update_expr:
        logger.error(f"Update failed for {user_id}: No valid fields")
        raise ValueError("No valid fields to update")
        
    response = table.update_item(
        Key={'id': user_id},
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeNames=expr_names if expr_names else None,
        ExpressionAttributeValues=expr_attrs,
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')

def delete_user(user_id: str):
    logger.info(f"Deleting user: {user_id}")
    table = get_table('Users')
    table.delete_item(Key={'id': user_id})
    return {"message": f"User {user_id} deleted"}
