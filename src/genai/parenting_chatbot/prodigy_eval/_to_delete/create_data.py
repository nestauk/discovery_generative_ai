import argparse
import json
import os

from dotenv import load_dotenv

from genai.streamlit_pages import parenting_page


parser = argparse.ArgumentParser(description="Name and location of output file")
parser.add_argument(
    "--out_dir",
    type=str,
    dest="out_dir",
    help="What value house are you trying to buy?",
    default="src/genai/parenting_chatbot/prodigy_eval/data/",
)

args, unknown = parser.parse_known_args()

FILEPATH = os.path.join(args.out_dir, "training_data.jsonl")

load_dotenv()

aws_key = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret = os.environ["AWS_SECRET_ACCESS_KEY"]
s3_path = os.environ["S3_BUCKET"]

# Sample data
data = [
    {
        "question": "How to baby-proof?",
        "answers": {
            "human": """
            <p>Baby-proofing your house is recommended for when your baby begins to explore, often when they’re beginning to crawl. Some baby-proofing precautions you can take include:</p>
             <ol>
        <li><strong>Secure Furniture</strong>: Anchor heavy furniture, like bookshelves and dressers, to the wall to prevent them from tipping over. Babies often try to pull themselves up using these items.</li>
        <li><strong>Outlet Covers</strong>: Use plastic covers for electrical outlets to prevent curious fingers from poking into them.</li>
        <li><strong>Cabinet and Drawer Latches</strong>: Install latches on cabinets and drawers, especially those containing cleaning products, chemicals, or small objects that can be swallowed.</li>
    </ol>
            """,
            "gpt4": "If a newborn has a fever, it's crucial to keep them hydrated and monitor their temperature. Seek medical attention promptly.",
            "rag": "Fever in a newborn can be concerning. It's recommended to consult with a healthcare professional right away.",
        },
    },
    {
        "question": "What should you do if a newborn has a fever?",
        "answers": {
            "human": "You should contact your pediatrician immediately as fever in a newborn can be a sign of a serious infection.",
            "gpt4": "If a newborn has a fever, it's crucial to keep them hydrated and monitor their temperature. Seek medical attention promptly.",
            "rag": "Fever in a newborn can be concerning. It's recommended to consult with a healthcare professional right away.",
        },
    },
    {
        "question": "How do you change a baby's nappy?",
        "answers": {
            "human": "The best place to change a nappy is on a changing mat or towel on the floor, particularly if you have more than one baby.",
            "gpt4": "Babies need frequent nappy changes.",
            "rag": "If your baby's nappy is dirty, use the nappy to clean off most of the poo from their bottom.",
        },
    },
    {
        "question": "How often should a newborn be bathed?",
        "answers": {
            "human": "Newborns don't need daily baths. Instead, you can bathe them every 2 to 3 days or as needed.",
            "gpt4": "It's usually recommended to bathe a newborn 2 to 3 times a week, but you can clean their face, neck, and hands daily.",
            "rag": "You don't need to give your newborn a bath every day. Two to three times a week is sufficient.",
        },
    },
    {
        "question": "What's the best position for a baby to sleep?",
        "answers": {
            "human": "The safest position for a baby is on their back. This reduces the risk of Sudden Infant Death Syndrome (SIDS).",
            "gpt4": "Babies should always be placed on their backs to sleep to minimize the risk of SIDS.",
            "rag": "Put your baby to sleep on their back to ensure safety and decrease the risk of SIDS.",
        },
    },
    {
        "question": "How can I soothe a crying newborn?",
        "answers": {
            "human": "Try swaddling, rocking, or offering a pacifier. Sometimes, the baby might just be hungry or need a diaper change.",
            "gpt4": "Newborns can be comforted by swaddling, gentle rocking, white noise, or even just holding them close.",
            "rag": "Consider swaddling, gentle motions, singing, or ensuring their basic needs are met to soothe a crying newborn.",
        },
    },
    {
        "question": "Is it normal for newborns to hiccup often?",
        "answers": {
            "human": "Yes, it's common for newborns to hiccup. It's usually not a cause for concern unless accompanied by other worrying symptoms.",
            "gpt4": "Hiccups are a normal part of a newborn's development and usually aren't a sign of any underlying issue.",
            "rag": "Newborns often hiccup, and it's generally considered normal. If you're concerned, consult your pediatrician.",
        },
    },
    {
        "question": "When should I introduce solid foods to my baby?",
        "answers": {
            "human": "Most experts recommend introducing solid foods around 6 months of age, but always consult with your pediatrician.",
            "gpt4": "Solid foods are typically introduced to babies at about 6 months old, but it's essential to look for signs of readiness and speak with a healthcare professional.",
            "rag": "Introduce solid foods to your baby around the 6-month mark, but ensure they show signs of readiness and get advice from a pediatrician.",
        },
    },
    {
        "question": "How can I help my newborn establish a sleep routine?",
        "answers": {
            "human": "Stick to a consistent bedtime routine, keep the room dark and quiet, and try to feed and change the baby before putting them down.",
            "gpt4": "Consistency is key. Develop a bedtime routine, reduce stimulation before sleep, and ensure they're well-fed and dry.",
            "rag": "Establishing a regular bedtime routine, reducing pre-sleep stimulation, and creating a calm environment can help.",
        },
    },
    {
        "question": "Why does my newborn sneeze so much?",
        "answers": {
            "human": "Newborns sneeze to clear their nasal and respiratory passages. It's normal and not necessarily a sign of illness.",
            "gpt4": "Sneezing is common in newborns as they clear out lint, dust, and mucus from their noses.",
            "rag": "Newborns often sneeze to clear tiny particles from their noses. It's a natural reflex and not a cause for concern.",
        },
    },
    {
        "question": "Can I take my newborn outside?",
        "answers": {
            "human": "Yes, but make sure to dress them appropriately for the weather and avoid direct sunlight. Avoid crowded places in the early weeks.",
            "gpt4": "Taking your newborn outside is fine, but ensure they're protected from the elements and avoid high traffic areas.",
            "rag": "It's good for newborns to get fresh air. Just ensure they're dressed properly and shielded from direct sun or extreme temperatures.",
        },
    },
]

# Saving data to a .jsonl file
with open(FILEPATH, "w") as file:
    for entry in data:
        file.write(json.dumps(entry) + "\n")

parenting_page.write_to_s3(
    aws_key,
    aws_secret,
    f"{s3_path}/prototypes/parenting-chatbot/prodigy_evaluation",
    "prodigy_training_data",
    data,
    how="w",
)