"""
NRSR Items
"""

import scrapy
from scrapy.loader.processors import Join, MapCompose, TakeFirst


def filter_whitespaces(value):
    return value.replace('\xa0', '').strip()


def filter_mailto(value):
    return value.replace('mailto:', '')    


def filter_vote(value):
    return value.strip()[1:-1]


class ClubItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    name = scrapy.Field(output_processor=TakeFirst())
    email = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    members = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())


class ClubMemberItem(scrapy.Item):
    external_id = scrapy.Field()
    membership = scrapy.Field()


class DailyClubItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    date = scrapy.Field(output_processor=TakeFirst())
    clubs = scrapy.Field()


class MemberItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    forename = scrapy.Field(output_processor=TakeFirst())
    surname = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    stood_for_party = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    born = scrapy.Field(output_processor=TakeFirst())
    nationality = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    residence = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    county = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    email = scrapy.Field(
        input_processor=MapCompose(filter_mailto),
        output_processor=Join()
    )
    images = scrapy.Field()
    image_urls = scrapy.Field()
    period_num = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())

    memberships = scrapy.Field()


class MemberChangeItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    date = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    change_type = scrapy.Field(output_processor=TakeFirst())
    change_reason = scrapy.Field(output_processor=TakeFirst())


class DebateAppearanceItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    debater_name = scrapy.Field(input_processor=MapCompose(filter_whitespaces), output_processor=TakeFirst())
    debater_party = scrapy.Field(input_processor=MapCompose(filter_whitespaces), output_processor=TakeFirst())
    debater_role = scrapy.Field(input_processor=MapCompose(filter_whitespaces), output_processor=TakeFirst())
    start = scrapy.Field(output_processor=TakeFirst())
    end = scrapy.Field(output_processor=TakeFirst())
    session_num = scrapy.Field(output_processor=TakeFirst())
    press_num = scrapy.Field()
    appearance_type = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    appearance_type_addition = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    text = scrapy.Field()
    video_short_url = scrapy.Field(output_processor=TakeFirst())
    video_long_url = scrapy.Field(output_processor=TakeFirst())


class HourOfQuestionsItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    status = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    question_by = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    question_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    recipient = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    question = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    answer_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    answer_by = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    answer = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    additional_question = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    additional_answer = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    url = scrapy.Field(output_processor=TakeFirst())


class AmendmentItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    press_num = scrapy.Field(output_processor=TakeFirst())
    session_num = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    submitter = scrapy.Field(output_processor=TakeFirst())
    other_submitters = scrapy.Field()
    date = scrapy.Field(output_processor=TakeFirst())
    signed_members = scrapy.Field()
    voting_external_id = scrapy.Field(output_processor=TakeFirst())
    attachments_names = scrapy.Field()
    attachments_urls = scrapy.Field()
    attachments = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())


class InterpellationItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    status = scrapy.Field(output_processor=TakeFirst())
    asked_by = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    description = scrapy.Field(output_processor=TakeFirst())
    recipients = scrapy.Field()
    date = scrapy.Field(output_processor=TakeFirst())
    interpellation_session_num = scrapy.Field(output_processor=TakeFirst())
    response_session_num = scrapy.Field(output_processor=TakeFirst())
    responded_by = scrapy.Field(output_processor=TakeFirst())
    press_num = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    attachments_names = scrapy.Field()
    attachments_urls = scrapy.Field()
    attachments = scrapy.Field()


class PressItem(scrapy.Item):
    type = scrapy.Field()
    title = scrapy.Field()
    press_num = scrapy.Field()
    group_num = scrapy.Field()
    period_num = scrapy.Field()
    press_type = scrapy.Field()
    date = scrapy.Field()
    attachments_names = scrapy.Field()
    attachments_urls = scrapy.Field()
    attachments = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())


class SessionItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    name = scrapy.Field(output_processor=TakeFirst())
    attachment_names = scrapy.Field()
    attachments_urls = scrapy.Field()
    attachments = scrapy.Field()
    program_points = scrapy.Field()
    period_num = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())

class VotingItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    topic = scrapy.Field(output_processor=TakeFirst())
    datetime = scrapy.Field(output_processor=TakeFirst())
    session_num = scrapy.Field(output_processor=TakeFirst())
    voting_num = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    press_num = scrapy.Field(output_processor=TakeFirst())
    press_url = scrapy.Field(output_processor=TakeFirst())
    result = scrapy.Field(output_processor=TakeFirst())
    votes = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())

class VotingVoteItem(scrapy.Item):
    external_id = scrapy.Field()
    vote = scrapy.Field(
        input_processor=MapCompose(filter_vote),
        output_processor=Join()
    )


class BillItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    proposer = scrapy.Field(output_processor=TakeFirst())
    delivered = scrapy.Field(output_processor=TakeFirst())
    press_num = scrapy.Field(output_processor=TakeFirst())
    current_state = scrapy.Field(output_processor=TakeFirst())
    current_result = scrapy.Field(output_processor=TakeFirst())
    category_name = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())


class BillStepItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    step_type = scrapy.Field(output_processor=TakeFirst())
    changes = scrapy.Field()
    bill_id = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    main_label = scrapy.Field()
    body_label = scrapy.Field()
    meeting_panel = scrapy.Field()
    meeting_session_num = scrapy.Field()
    meeting_resolution = scrapy.Field()
    committees_label = scrapy.Field()
    slk_label = scrapy.Field()
    coordinator_label = scrapy.Field()
    coordinator_meeting_date = scrapy.Field()
    coordinator_name = scrapy.Field()
    step_result = scrapy.Field()
    discussed_label = scrapy.Field()
    sent_standpoint = scrapy.Field()
    sent_label = scrapy.Field()
    act_num_label = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())


class BillStepChangeItem(scrapy.Item):
    date = scrapy.Field()
    author = scrapy.Field()
    detail = scrapy.Field()
    attachment_title = scrapy.Field()
    attachment_url = scrapy.Field()
