import os

from fun_with_maps.utils import utils


def test_generate_pdf_report_custom_path(tmp_path):
    utils.clear_plot_tracker()
    utils.set_country_info("Testland")
    image_path = tmp_path / "img.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    utils._plot_tracker["plots"].append(
        {"title": "t", "description": "d", "filepath": str(image_path)}
    )

    os.makedirs("docs", exist_ok=True)
    pdf_path = os.path.join("docs", "Testland_analysis_report.pdf")
    utils.generate_pdf_report(output_filename=pdf_path)

    assert os.path.exists(pdf_path)
    os.remove(pdf_path)
