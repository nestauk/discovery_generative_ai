from typing import Dict, Iterator
import openai
from dotenv import load_dotenv
import os
load_dotenv()
# OpenAI settings
openai.api_key = os.environ["OPENAI_API_KEY"]

AOL = [
    "Communication and Language",
    "Personal, Social and Emotional Development",
    "Physical Development",
    "Literacy",
    "Mathematics",
    "Understanding the World",
    "Expressive Arts and Design",
]

AREAS_OF_LEARNING_DESC = {
    "Communication and Language": """##Communication and Language##\nThe development of children’s spoken language underpins all seven areas of learning and development. Children’s back-and-forth interactions from an early age form the foundations for language and cognitive development. The number and quality of the conversations they have with adults and peers throughout the day in a language-rich environment is crucial. By commenting on what children are interested in or doing, and echoing back what they say with new vocabulary added, practitioners will build children's language effectively. Reading frequently to children, and engaging them actively in stories, non-fiction, rhymes and poems, and then providing them with extensive opportunities to use and embed new words in a range of contexts, will give children the opportunity to thrive. Through conversation, story-telling and role play, where children share their ideas with support and modelling from their teacher, and sensitive questioning that invites them to elaborate, children become comfortable using a rich range of vocabulary and language structures.""",
    "Personal, Social and Emotional Development": """##Personal, Social and Emotional Development##\nChildren’s personal, social and emotional development (PSED) is crucial for children to lead healthy and happy lives, and is fundamental to their cognitive development. Underpinning their personal development are the important attachments that shape their social world. Strong, warm and supportive relationships with adults enable children to learn how to understand their own feelings and those of others. Children should be supported to manage emotions, develop a positive sense of self, set themselves simple goals, have confidence in their own abilities, to persist and wait for what they want and direct attention as necessary. Through adult modelling and guidance, they will learn how to look after their bodies, including healthy eating, and manage personal needs independently. Through supported interaction with other children, they learn how to make good friendships, co-operate and resolve conflicts peaceably. These attributes will provide a secure platform from which children can achieve at school and in later life.""",
    "Physical Development": """##Physical Development##\nPhysical activity is vital in children’s all-round development, enabling them to pursue happy, healthy and active lives7. Gross and fine motor experiences develop incrementally throughout early childhood, starting with sensory explorations and the development of a child’s strength, co-ordination and positional awareness through tummy time, crawling and play movement with both objects and adults. By creating games and providing opportunities for play both indoors and outdoors, adults can support children to develop their core strength, stability, balance, spatial awareness, co-ordination and agility. Gross motor skills provide the foundation for developing healthy bodies and social and emotional well-being. Fine motor control and precision helps with hand-eye co-ordination, which is later linked to early literacy. Repeated and varied opportunities to explore and play with small world activities, puzzles, arts and crafts and the practice of using small tools, with feedback and support from adults, allow children to develop proficiency, control and confidence.""",
    "Literacy": """##Literacy##\nIt is crucial for children to develop a life-long love of reading. Reading consists of two dimensions: language comprehension and word reading. Language comprehension (necessary for both reading and writing) starts from birth. It only develops when adults talk with children about the world around them and the books (stories and non-fiction) they read with them, and enjoy rhymes, poems and songs together. Skilled word reading, taught later, involves both the speedy working out of the pronunciation of unfamiliar printed words (decoding) and the speedy recognition of familiar printed words. Writing involves transcription (spelling and handwriting) and composition (articulating ideas and structuring them in speech, before writing).""",
    "Mathematics": """##Mathematics##\nDeveloping a strong grounding in number is essential so that all children develop the necessary building blocks to excel mathematically. Children should be able to count confidently, develop a deep understanding of the numbers to 10, the relationships between them and the patterns within those numbers. By providing frequent and varied opportunities to build and apply this understanding - such as using manipulatives, including small pebbles and tens frames for organising counting - children will develop a secure base of knowledge and vocabulary from which mastery of mathematics is built. In addition, it is important that the curriculum includes rich opportunities for children to develop their spatial reasoning skills across all areas of mathematics including shape, space and measures. It is important that children develop positive attitudes and interests in mathematics, look for patterns and relationships, spot connections, ‘have a go’, talk to adults and peers about what they notice and not be afraid to make mistakes.""",
    "Understanding the World": """##Understanding the World##\nUnderstanding the world involves guiding children to make sense of their physical world and their community. The frequency and range of children’s personal experiences increases their knowledge and sense of the world around them – from visiting parks, libraries and museums to meeting important members of society such as police officers, nurses and firefighters. In addition, listening to a broad selection of stories, non-fiction, rhymes and poems will foster their understanding of our culturally, socially, technologically and ecologically diverse world. As well as building important knowledge, this extends their familiarity with words that support understanding across domains. Enriching and widening children’s vocabulary will support later reading comprehension.""",
    "Expressive Arts and Design": """##Expressive Arts and Design##\nThe development of children’s artistic and cultural awareness supports their imagination and creativity. It is important that children have regular opportunities to engage with the arts, enabling them to explore and play with a wide range of media and materials. The quality and variety of what children see, hear and participate in is crucial for developing their understanding, self-expression, vocabulary and ability to communicate through the arts. The frequency, repetition and depth of their experiences are fundamental to their progress in interpreting and appreciating what they hear, respond to and observe.""",
}   


def generate_response(prompt: Iterator[Dict[str, str]]):
    """Generate a response from prompt"""
    return openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=prompt,
    temperature=0.5,
    max_tokens=1000,
).to_dict()


def activities_prompt(
    msg: str,
    n_results: int = 5,
    location: str = "Indoors or Outdoors",
    areas_of_learning: Iterator[str] = AOL,      
) -> Iterator[Dict[str, str]]:
    """
    Placeholder code for generating a prompt for activities

    Args:
        msg (str): message text
        n_results (int, optional): number of results to generate. Defaults to 5.
        location (str, optional): location of the activity. Defaults to "Indoors or Outdoors".
        areas_of_learning (Iterator[str], optional): areas of learning. Defaults to all areas of learning.

    Returns:
        Iterator[Dict[str, str]]: Prompt for generating activities    
    """

    # Define activities of learning     
    areas_of_learning_text = [v for k, v in AREAS_OF_LEARNING_DESC.items() if k in areas_of_learning]
    # Define prompts
    messages = [
        {
            "role": "system",
            "content": "You are a very creative and highly educated assistant who loves designing early year education programmes.",
        },
        {
            "role": "user",
            "content": f"""###Context###The UK's Early Years Foundation Stage framework recommends that educational programmes must involve activities and experiences for children, as set out under each of the areas of learning described below.\n\n##Areas of Learning###\n{areas_of_learning_text}\n\n###Instructions###\nI am an early years educator and I am working with children 3-4 years old. I will describe you a situation in the ###Description### section. Please propose conversations and activities I could do with the children to extend their learning.\n\nTypes of activities:\n- Conversations: Asking them questions about the topic\n- Puzzles, games, role play, arts and crafts\n\n###Formatting###\nReturn the proposed activities in the following format:\n\n## Conversations\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n## Games and Crafts\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n""",  # noqa: B950
        },
        {
            "role": "user",
            "content": f"###Requirements for the activities###\n1. Your suggestions must be fun and engaging for the children.\n2. Your suggestions must be novel, inspiring and memorable.\n3. You must suggest topics for conversation with the children and questions to ask them.\n4. Your proposed activities engage children in the following Areas of Learning: {areas_of_learning}.\n5. You must generate {n_results} activities.\n6. Your proposed activities must be played {location}",  # noqa: B950
        },
    ]     
    messages.append({"role": "user", "content": f"###Description###\n{msg}\n\n###Activities###\n"})  
    return messages