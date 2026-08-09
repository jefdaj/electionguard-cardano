import datetime
import json
import re
from dataclasses import dataclass, asdict
from typing import Optional
import electionguard as eg
from enum import Enum, unique

"""Minimal manifest options to support use in demos. Deliberately unstructured
for now in order to flexibly try things. Will be gradually codified and
expanded to cover more use cases as needed. Each class can load example data
from a JSON config and render it to a dict. The dict should be loadable as the
corresponding ElectionGuard type.
"""

# TODO include policy id somewhere
# TODO later, use end date to determine when subscribers should time out


@unique
class EgcContestType(Enum):
    office     = "office"     # question=office, candidates=candidates
    referendum = "referendum" # question=question, candidates=yes/no


def sanitize_key(unsanitized: str) -> str:
    s = unsanitized.strip()
    s = re.sub(r"\s+", "-", s)     # whitespace -> underscore
    s = re.sub(r"[^\w\_.]", "", s) # keep alnum, _, -, .
    s = s.lower()                  # lowercase
    if len(s) == 0:
        raise Exception(f'failed to sanitize_key: "{unsanitized}"')
    return s


@dataclass
class EgcContest:
    type: EgcContestType
    question: str
    answers: Optional[ list[str] ] = None # none for referendum

    # TODO from_cfg_dict?
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type     = EgcContestType(data['type']),
            question = data['question'],
            answers  = data['answers'],
        )

    def to_dict(self):
        return {
            'type': self.type.value,
            'question': self.question,
            'answers': self.answers,
        }

    @classmethod
    def from_json(cls, data: str):
        return cls.from_dict(json.loads(data))

    def contest_id(self) -> str:
        return f'{self.type.value}-{sanitize_key(self.question)}'

    def candidates(self) -> list[dict]:
        candidates = []
        match self.type:

            case EgcContestType.referendum:
                answers = {
                    'affirmative': 'Yes',
                    'negative':    'No',
                }
                for (id_suffix, answer_text) in answers.items():
                    answer_dict = {
                        "object_id":   f'{self.contest_id()}-{id_suffix}',
                        "party_id":    None,
                        "image_uri":   None,
                        "is_write_in": None,
                        "text": { "text": [{"value": answer_text, "language": "en"}] },
                    }
                    candidates.append(answer_dict)

            case EgcContestType.office:
                for candidate_name in self.answers:
                    answer_dict = {
                        "object_id":   f'candidate-{sanitize_key(candidate_name)}',
                        "party_id":    None,
                        "image_uri":   None,
                        "is_write_in": None,
                        "text": { "text": [{"value": candidate_name, "language": "en"}] },
                    }
                    candidates.append(answer_dict)

            case _: raise NotImplementedError
        return candidates

    def ballot_selections(self):
        selections = []
        for (seq_order, candidate) in enumerate(self.candidates(), start=1):
            selection = {
                'object_id': f'{candidate['object_id']}-selection',
                'sequence_order': seq_order,
                'candidate_id': candidate['object_id'],
            }
            selections.append(selection)
        return selections

    def to_eg_dict(self, sequence_order: int) -> dict:
        contest_dict = {
            "object_id":             self.contest_id(),
            "sequence_order":        sequence_order,
            "electoral_district_id": "electionguard-cardano-test-county",
            "vote_variation":        "one_of_m",
            "number_elected":        1,
            "votes_allowed":         1,
            "name":                  self.question,
            "ballot_selections":     self.ballot_selections(),
        }
        return contest_dict


@dataclass(unsafe_hash=True)
class EgcManifest:
    contests: list[EgcContest]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            contests = [
                EgcContest.from_dict(c)
                for c in data['contests']
            ]
        )

    @classmethod
    def from_json(cls, data: str):
        return cls.from_dict(json.loads(data))

    def to_dict(self):
        return {
            'contests': [c.to_dict() for c in self.contests]
        }

    def to_eg(self) -> eg.Manifest:
        eg_json_str = json.dumps( self.to_eg_dict() )
        eg_manifest = eg.serialize.from_raw(eg.Manifest, eg_json_str)
        assert eg_manifest.is_valid()
        return eg_manifest

    def to_eg_dict(self) -> dict:

        now = datetime.datetime.now(datetime.UTC)

        county_id = "electionguard-cardano-test-county"

        candidates = []
        for contest in self.contests:
            candidates += [
                c for c in contest.candidates()
                if not c in candidates
            ]

        contests = [
            contest.to_eg_dict(sequence_order=n)
            for (n, contest) in enumerate(self.contests, start=1)
        ]

        # TODO can parties be empty?
        manifest_dict = {
            'election_scope_id': 'electionguard-cardano-test-manifest',
            'spec_version': '1.0', # TODO is this right?
            'type': 'other',
            'start_date': str(now),
            'end_date': str(now + datetime.timedelta(days=2, hours=12)),
            'geopolitical_units': [{
                "object_id": county_id,
                "name": "ElectionGuard + Cardano Test County",
                "type": "municipality",
                "contact_information": None,
            }],
            "parties": [{
                "object_id": "N/A",
                "name": {
                    "text": []
                },
                "abbreviation": None,
                "color": None,
                "logo_uri": None
            }],
            "candidates": candidates,
            "contests": contests,
            "ballot_styles": [{
                "object_id": "ballot-style-01",
                "geopolitical_unit_ids": [county_id],
                "party_ids": None,
                "image_uri": None
            }],
            "ballot_title": None,
            "ballot_subtitle": None,
            "name": {
                "text": [
                    {
                        "value": "ElectionGuard + Cardano Test Election",
                        "language": "en"
                    },
                ]
            },
            "contact_information": None
        }
        return manifest_dict
