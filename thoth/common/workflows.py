# thoth-common
# Copyright(C) 2019 Marek Cermak
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import random

from typing import Dict
from typing import Optional
from typing import Union

from argo.workflows import client
from argo.workflows import models

from .exceptions import ConfigurationError
from .exceptions import WorkflowError

from .openshift import OpenShift


class Workflow(models.V1alpha1Workflow):
    """Argo Workflow instance.

    This is a subclass of argo.workflows V1alpha1Workflow model
    which provides a convenient set of methods to make workflow
    managemend easier.
    """

    def __init__(
        self, api_version=None, kind=None, metadata=None, spec=None, status=None
    ):
        super().__init__(
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )

        self.__dict__.update(self.metadata)

    @classmethod
    def from_dict(cls, wf: dict) -> "Workflow":
        """Create a Workflow from a dict."""

    @classmethod
    def from_file(cls, fp: str) -> "Workflow":
        """Create a Workflow from a file."""

    @classmethod
    def from_url(cls, url: str) -> "Workflow":
        """Create a Workflow from a remote file."""


class WorkflowManager:
    """Argo Workflow manager."""

    def __init__(
        self, ocp_client: Optional[OpenShift] = None, ocp_config: Optional[Dict] = None
    ):
        ocp_config = ocp_config or {}

        self.openshift = ocp_client or OpenShift(**ocp_config)
        self.api = client.V1alpha1Api(client.ApiClient(self.openshift.configuration))

    def _submit_workflow(
        self,
        namespace: Optional[str],
        wf: Union[models.V1alpha1Workflow, dict],
        *,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Submit an Argo Workflow to a given namespace."""
        parameters = parameters or {}

        if not isinstance(wf, Workflow):
            wf = Workflow.from_dict(wf)

        new_parameters: List[models.V1alpha1Parameter] = []
        for name, value in parameters.items():
            param = models.V1alpha1Parameter(name=name, value=value)
            new_parameters.append(param)

        for p in wf.spec.arguments.parameters:
            if p.name in parameters:
                continue  # overridden
            elif not p.value and not p.default:
                raise WorkflowError(f"Missing required workflow parameter {p.name}")

            new_parameters.append(p)

        wf.spec.arguments.parameters = new_parameters

        # submit the workflow
        created = self.api.create_namespaced_workflow(namespace, wf)

        return created.name
