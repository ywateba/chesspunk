import uuid
from serverless.dynamodb import get_table
from serverless.logger import logger

def list_communities():
    logger.debug("Scanning Communities table")
    table = get_table('Communities')
    return table.scan().get('Items', [])

def get_community(comm_id: str):
    table = get_table('Communities')
    return table.get_item(Key={'id': comm_id}).get('Item')

def create_community(body: dict):
    name = body.get('name')
    owner_id = body.get('owner_id')
    if not name or not owner_id:
        logger.error("Failed creating community: missing name/owner_id")
        raise ValueError("Missing name or owner_id")
        
    comm_id = str(uuid.uuid4())
    logger.info(f"Creating Community {name} under owner {owner_id}")
    table = get_table('Communities')
    
    item = {
        'id': comm_id,
        'name': name,
        'description': body.get('description', ''),
        'owner_id': owner_id,
        'members': [owner_id]
    }
    table.put_item(Item=item)
    return item

def add_member(comm_id: str, body: dict):
    member_id = body.get('member_id')
    if not member_id:
        raise ValueError("Missing member_id")
        
    table = get_table('Communities')
    response = table.update_item(
        Key={'id': comm_id},
        UpdateExpression="SET members = list_append(if_not_exists(members, :empty_list), :member)",
        ExpressionAttributeValues={
            ":member": [member_id],
            ":empty_list": []
        },
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')
