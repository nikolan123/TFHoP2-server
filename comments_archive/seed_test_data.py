import argparse
import random
import sys
from pathlib import Path

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIRECTORY))

from database import record_comment, record_vote


POLL_OPTION_COUNTS = {1: 7, 3: 5, 4: 6, 5: 8, 6: 3}
NAMES = [
    "Chell",
    "Atlas",
    "P-body",
    "GLaDOS",
    "Wheatley",
    "Cave Johnson",
    "Caroline",
    "Doug Rattmann",
]
COMMENTS = [
    "This is a test comment about portals and science.",
    "The enrichment center reminds you that this entry is junk test data.",
    "I enjoyed the behind-the-scenes material.",
    "Testing the comment pagination. The cake remains inconclusive.",
    "Speedy comment goes in, speedy comment comes out.",
    "Portal preservation test successful.",
    "Combustible lemons would improve this feedback form.",
    "Another completely scientific test submission.",
]


def inject_test_data(comment_count, vote_count):
    randomizer = random.Random(2)

    for index in range(comment_count):
        record_comment(
            randomizer.choice(NAMES),
            f"{randomizer.choice(COMMENTS)} [TEST {index + 1}]",
            f"192.0.2.{index % 254 + 1}",
        )

    poll_ids = list(POLL_OPTION_COUNTS)
    for index in range(vote_count):
        poll_id = randomizer.choice(poll_ids)
        record_vote(
            poll_id,
            randomizer.randrange(POLL_OPTION_COUNTS[poll_id]),
            f"198.51.100.{index % 254 + 1}",
        )

    print(f"Inserted {comment_count} test comments and {vote_count} test votes into portal.db.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert junk data for local UI testing.")
    parser.add_argument("--comments", type=int, default=35)
    parser.add_argument("--votes", type=int, default=250)
    arguments = parser.parse_args()

    if arguments.comments < 0 or arguments.votes < 0:
        parser.error("counts cannot be negative")

    inject_test_data(arguments.comments, arguments.votes)
