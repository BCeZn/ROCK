import pytest

from rock.deployments.constants import Port, Status
from rock.deployments.status import PhaseStatus, ServiceStatus


@pytest.mark.asyncio
async def test_service_status_init():
    service_status = ServiceStatus()
    assert service_status.get_phase("image_pull").status == Status.WAITING
    assert service_status.get_phase("docker_run").status == Status.WAITING
    service_status.update_status("image_pull", Status.SUCCESS, "image pulled")
    assert service_status.phases is not None


@pytest.mark.asyncio
async def test_phase_status_init():
    phase_status = PhaseStatus()
    assert phase_status.status == Status.WAITING
    assert phase_status.message == "waiting"

    phase_status = PhaseStatus(status=Status.FAILED, message="docker run failed")
    assert phase_status.status == Status.FAILED
    assert phase_status.message == "docker run failed"


@pytest.mark.asyncio
async def test_port_mapping():
    service_status = ServiceStatus()
    assert service_status.port_mapping is not None
    assert len(service_status.port_mapping.keys()) == 0
    service_status.add_port_mapping(Port.SSH, 10000)
    service_status.add_port_mapping(Port.PROXY, 65532)
    assert len(service_status.port_mapping.keys()) == 2
    assert service_status.get_mapped_port(Port.SSH) == 10000
    assert service_status.get_mapped_port(Port.PROXY) == 65532

    port_mapping = service_status.get_port_mapping()
    assert port_mapping[Port.SSH] == 10000
    assert port_mapping[Port.PROXY] == 65532


@pytest.mark.asyncio
def test_json_serialize():
    service_status = ServiceStatus()
    service_status.update_status("image_pull", Status.SUCCESS, "image pulled")
    service_status.add_port_mapping(Port.SSH, 10000)
    status_dict = service_status.to_dict()
    assert status_dict.get("port_mapping").get(Port.SSH) == 10000

    json_status = ServiceStatus.from_dict(status_dict)
    assert json_status is not None
    assert json_status.get_mapped_port(Port.SSH) == 10000
