#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import copy
import os

from parlai.core.message import Message
from parlai.core.opt import Opt
from parlai.core.teachers import FixedDialogTeacher, ParlAIDialogTeacher
from parlai.tasks.style_gen.build import (
    build_personality_list,
    build_style_labeled_datasets,
    get_style_labeled_data_folder,
    TASK_FOLDER_NAME,
)
from parlai.tasks.wrapper.agents import AbstractWrapperTeacher


def get_style_labeled_data_path(opt: Opt, base_task: str) -> str:
    """
    Return the filepath for the specified datatype of the specified base task, with an
    Image-Chat personality attached to each example.
    """
    build_style_labeled_datasets(opt)
    # Build the data if it doesn't exist.
    dt = opt['datatype'].split(':')[0]
    return os.path.join(
        get_style_labeled_data_folder(opt['datapath']), base_task, dt + '.txt'
    )


def get_personality_list_path(opt: Opt) -> str:
    """
    Return the path to a list of personalities in the Image-Chat train set.
    """
    build_personality_list(opt)
    # Build the data if it doesn't exist.
    return os.path.join(opt['datapath'], TASK_FOLDER_NAME, 'personality_list.txt')


class LabeledBlendedSkillTalkTeacher(ParlAIDialogTeacher):
    """
    Teacher for blended_skill_talk:BlendedSkillTalk, with Image-Chat personalities added
    to examples.
    """

    def __init__(self, opt, shared=None):
        opt['parlaidialogteacher_datafile'] = get_style_labeled_data_path(
            opt=opt, base_task='blended_skill_talk'
        )
        super().__init__(opt, shared=shared)


class LabeledConvAI2PersonaTopicifierTeacher(ParlAIDialogTeacher):
    """
    Teacher for blended_skill_talk:ConvAI2PersonaTopicifier, with Image-Chat
    personalities added to examples.
    """

    def __init__(self, opt, shared=None):
        opt['parlaidialogteacher_datafile'] = get_style_labeled_data_path(
            opt=opt, base_task='blended_skill_talk:ConvAI2PersonaTopicifierTeacher'
        )
        super().__init__(opt, shared=shared)


class LabeledEDPersonaTopicifierTeacher(ParlAIDialogTeacher):
    """
    Teacher for blended_skill_talk:EDPersonaTopicifier, with Image-Chat personalities
    added to examples.
    """

    def __init__(self, opt, shared=None):
        opt['parlaidialogteacher_datafile'] = get_style_labeled_data_path(
            opt=opt, base_task='blended_skill_talk:EDPersonaTopicifierTeacher'
        )
        super().__init__(opt, shared=shared)


class LabeledWoWPersonaTopicifierTeacher(ParlAIDialogTeacher):
    """
    Teacher for blended_skill_talk:WoWPersonaTopicifier, with Image-Chat personalities
    added to examples.
    """

    def __init__(self, opt, shared=None):
        opt['parlaidialogteacher_datafile'] = get_style_labeled_data_path(
            opt=opt, base_task='blended_skill_talk:WoWPersonaTopicifierTeacher'
        )
        super().__init__(opt, shared=shared)


class PrevCurrUttStyleTeacher(AbstractWrapperTeacher):
    """
    Serving examples for use with projects.style_gen.classifier:ClassifierAgent.

    This teacher will replace message['text'] with a concatenation of the last utterance
    in message['text'] and message['labels'][0], and it will replace message['labels']
    with [message['personality']]. This is to allow for training/evaluation of
    projects.style_gen.classifier:ClassifierAgent, which typically classifies the style
    of an utterance given that utterance and the previous one as context.

    Because the dialogue history is effectively overwritten by this action, all episodes
    will be flattened into one example each.
    """

    def __init__(self, opt: Opt, shared=None):
        super().__init__(opt, shared)
        assert isinstance(self.task, FixedDialogTeacher)

    def act(self):
        """
        Act on the previous observation.
        """

        orig_act = self.task.get_orig_action()

        # Edit the fields of the act
        new_act = copy.deepcopy(orig_act)
        if 'labels' in orig_act:
            labels = orig_act['labels']
            if len(labels) != 1:
                raise ValueError(
                    f'{type(self).__name__} can only be used with one label!'
                )
            assert '\n' not in labels[0]
            # Classifier will not expect more than 1 newline in context
            new_act.force_set(
                'text', new_act['text'].split('\n')[-1] + '\n' + labels[0]
            )
            new_act.force_set('labels', [new_act['personality']])
        else:
            assert 'text' not in orig_act and orig_act['episode_done'] is True
        new_act.force_set('episode_done', True)  # Clear the dialogue history

        # Process the action
        final_action = self.task.process_action(orig_act)

        return final_action
