import io
from pathlib import Path
from turtle import pu

import pandas as pd
import pymupdf  # PyMuPDF


class DataIngestionService:

    ALLOWED_EXTENSIONS = {
        ".csv",
        ".xlsx",
        ".xls",
        ".pdf",
    }

    def validate_file(
        self,
        filename: str,
    ):
        extension = Path(filename).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            return {
                "valid": False,
                "message": (
                    "Unsupported file format. "
                    "Please upload CSV, Excel, or PDF."
                ),
            }

        return {
            "valid": True,
            "extension": extension,
        }

    def read_file(
        self,
        filename: str,
        content: bytes,
    ):
        validation = self.validate_file(
            filename
        )

        if not validation["valid"]:
            return validation

        extension = validation["extension"]

        try:

            # -----------------------------------------
            # CSV
            # -----------------------------------------

            if extension == ".csv":

                dataframe = pd.read_csv(
                    io.BytesIO(content)
                )

                return {
                    "valid": True,
                    "file_type": "csv",
                    "dataframe": dataframe,
                }

            # -----------------------------------------
            # Excel
            # -----------------------------------------

            if extension in {".xlsx", ".xls"}:

                dataframe = pd.read_excel(
                    io.BytesIO(content)
                )

                return {
                    "valid": True,
                    "file_type": "excel",
                    "dataframe": dataframe,
                }

            # -----------------------------------------
            # PDF
            # -----------------------------------------

            if extension == ".pdf":

                pdf_document = pymupdf.open(
                    stream=content,
                    filetype="pdf",
                )

                pages = []

                for page_number, page in enumerate(
                    pdf_document
                ):
                    text = page.get_text()

                    pages.append(
                        {
                            "page": page_number + 1,
                            "text": text,
                        }
                    )

                pdf_document.close()

                full_text = "\n".join(
                    page["text"]
                    for page in pages
                )

                if not full_text.strip():
                    return {
                        "valid": False,
                        "message": (
                            "The PDF does not contain "
                            "extractable text. "
                            "Scanned PDFs will require "
                            "OCR processing."
                        ),
                    }

                return {
                    "valid": True,
                    "file_type": "pdf",
                    "text": full_text,
                    "pages": pages,
                }

        except Exception as exc:

            return {
                "valid": False,
                "message": (
                    f"Unable to read the file: {exc}"
                ),
            }

        return {
            "valid": False,
            "message": "Unable to process the file.",
        }

    def inspect_dataframe(
        self,
        dataframe: pd.DataFrame,
    ):
        dataframe.columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        preview = (
            dataframe
            .head(5)
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        return {
            "row_count": len(dataframe),
            "column_count": len(
                dataframe.columns
            ),
            "columns": [
                str(column)
                for column in dataframe.columns
            ],
            "preview": preview,
        }

    def inspect_pdf(
        self,
        text: str,
        pages: list,
    ):
        return {
            "page_count": len(pages),
            "character_count": len(text),
            "preview": text[:5000],
        }


data_ingestion_service = DataIngestionService()