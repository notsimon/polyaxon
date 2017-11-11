# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.functional import cached_property

from polyaxon_schemas.polyaxonfile.specification import Specification

from clusters.constants import ExperimentLifeCycle
from libs.models import DiffModel
from projects.signals import new_spec


class Project(DiffModel):
    """A model that represents a set of experiments to solve a specific problem."""
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='projects')
    name = models.CharField(
        max_length=256,
        help_text='Name of the project.')
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Description of the project.')
    is_public = models.BooleanField(default=True, help_text='If project is public or private.')

    def __str__(self):
        return self.name


class PolyaxonSpec(DiffModel):
    """A model that saves PolyaxonSpec/Polyaxonfiles."""
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='specs')
    content = models.TextField(help_text='The yaml content of the polyaxonfile/specification.')
    project = models.ForeignKey(
        Project,
        related_name='specs',
        help_text='The project this polyaxonfile belongs to.')

    @cached_property
    def parsed_content(self):
        return Specification.read(self.content)

    @cached_property
    def concurrency(self):
        return self.parsed_content.settings.conccurrent_experiments

    @property
    def running_experiments(self):
        return self.experiments.filter(status__status__in=ExperimentLifeCycle.RUNNING_STATUS)

    @property
    def can_start_new_experiment(self):
        # We need to check if we are allowed to start the experiment
        # If the polyaxonfile has concurrency
        # we need to need to check how many experiments are running
        return self.concurrency > self.running_experiments.count()


# post_save.connect(new_spec, sender=PolyaxonSpec, dispatch_uid="spec_saved")
