from prevent_sleep import install_service


def test_install_service(out_dir):
    assert install_service.install_service(out_dir) is None
