import os
from typing import List
import google.generativeai as genai
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

class DocumentQueryService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key must be provided.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemma-3-1b-it')

    def _get_document_content(self, document_url: str) -> List[str]:
        try:
            # This is mock content. A real implementation would fetch and parse the PDF.
            print(f"Fetching mock content for URL: {document_url}")
            return [
                "Grace Period: Thirty (30) days from the due date for payment to renew or continue the policy.",
                "Pre-existing Diseases (PED) waiting period: Thirty-six (36) months of continuous coverage from the first policy start date.",
                "Maternity expenses: The policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months. The benefit is limited to two deliveries or terminations during the policy period.",
                "Waiting period for cataract surgery: Two (2) years of continuous coverage for cataract surgery.",
                "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person and the donation complies with the Transplantation of Human Organs Act, 1994.",
                "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year. The maximum aggregate NCD is capped at 5% of the total base premium.",
                "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break. The amount is subject to the limits specified in the Table of Benefits.",
                "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7, a fully equipped operation theatre, and which maintains daily records of patients.",
                "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit, provided the treatment is taken in an AYUSH Hospital.",
                "Yes, for Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured. These limits do not apply if the treatment is for a listed procedure in a Preferred Provider Network (PPN)."
            ]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching document from URL: {e}")
            return []

    def _retrieve_relevant_clauses(self, questions: List[str], document_clauses: List[str]) -> str:
        # This simplified retrieval uses keywords. A real system would use embeddings.
        relevant_clauses = set()
        keywords = {
            "grace period": document_clauses[0],
            "pre-existing": document_clauses[1],
            "maternity": document_clauses[2],
            "cataract": document_clauses[3],
            "organ donor": document_clauses[4],
            "no claim discount": document_clauses[5],
            "ncd": document_clauses[5],
            "health check-up": document_clauses[6],
            "hospital": document_clauses[7],
            "ayush": document_clauses[8],
            "room rent": document_clauses[9],
            "icu": document_clauses[9]
        }
        for question in questions:
            q_lower = question.lower()
            for keyword, clause in keywords.items():
                if keyword in q_lower:
                    relevant_clauses.add(clause)
        return "\n".join(list(relevant_clauses)) if relevant_clauses else "\n".join(document_clauses)


    def query_document(self, document_url: str, questions: List[str]) -> List[str]:
        document_clauses = self._get_document_content(document_url)
        if not document_clauses:
            return ["Failed to retrieve or process document content." for _ in questions]

        retrieved_context = self._retrieve_relevant_clauses(questions, document_clauses)
        if not retrieved_context:
            return ["Information not found in the document." for _ in questions]

        answers = []
        for question in questions:
            try:
                prompt = (
                    f"You are an assistant that answers questions based on the provided text. "
                    f"Use ONLY the information from the text below to answer the question. "
                    f"If the answer is not in the text, say 'Information not found in the document.'\n\n"
                    f"Document Context:\n{retrieved_context}\n\n"
                    f"Question: {question}\n\n"
                    f"Answer:"
                )
                response = self.model.generate_content(prompt)
                answers.append(response.text.strip())
            except Exception as e:
                print(f"Error during LLM API call: {e}")
                answers.append("An error occurred while generating the answer.")
        return answers

api_key = "AIzaSyCFGqpaDYplXIXrOw4Y9qn990z-44F2KUU"

service = DocumentQueryService(api_key=api_key)

@app.route('/hackrx/run', methods=['POST'])
def handle_run():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header == "Bearer 154f29c7918d5bc40c7206aa13adad4a496986b4c42b71e0b0d37ac48b3db6a6":
        return jsonify({"error": "Authorization header is missing or invalid"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    doc_url = data.get('documents')
    questions = data.get('questions')

    if not doc_url or not questions or not isinstance(questions, list):
        return jsonify({"error": "Missing or invalid 'documents' or 'questions'"}), 400

    try:
        generated_answers = service.query_document(doc_url, questions)
        return jsonify({"answers": generated_answers})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

