import uuid
from serverless.dynamodb import get_table
from serverless.logger import logger

def list_posts():
    logger.debug("Scanning Social Posts table")
    table = get_table('Social')
    return table.scan().get('Items', [])

def get_post(post_id: str):
    table = get_table('Social')
    return table.get_item(Key={'id': post_id}).get('Item')

def create_post(body: dict):
    author_id = body.get('author_id')
    content = body.get('content')
    if not author_id or not content:
        logger.error("Failed creating post: missing payload data")
        raise ValueError("Missing author_id or content")
        
    post_id = str(uuid.uuid4())
    logger.info(f"Creating new post by {author_id}: {post_id}")
    table = get_table('Social')
    
    item = {
        'id': post_id,
        'author_id': author_id,
        'content': content,
        'entity_type': body.get('entity_type', 'post'),
        'entity_id': body.get('entity_id'),
        'comments': []
    }
    table.put_item(Item=item)
    return item

def create_comment(post_id: str, body: dict):
    author_id = body.get('author_id')
    content = body.get('content')
    if not author_id or not content:
        raise ValueError("Missing author_id or content")
        
    comment_id = str(uuid.uuid4())
    table = get_table('Social')
    
    comment_obj = {
        'id': comment_id,
        'author_id': author_id,
        'content': content
    }
    
    response = table.update_item(
        Key={'id': post_id},
        UpdateExpression="SET comments = list_append(if_not_exists(comments, :empty_list), :comment)",
        ExpressionAttributeValues={
            ":comment": [comment_obj],
            ":empty_list": []
        },
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')
