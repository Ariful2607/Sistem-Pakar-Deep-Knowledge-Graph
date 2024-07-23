from flask import Flask, jsonify, render_template, request
from neo4j import GraphDatabase
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define connection details for remote Neo4j instance (GCP)
# uri = "bolt://34.101.192.24:7687"
# user = "neo4j"
# password = "unej1234"

# Define connection details for remote Neo4j instance
uri = "bolt://ricekg.extani.web.id:7687"  # Update with the new domain and correct port
user = "neo4j"
password = "unej1234"

# Create a driver instance
driver = GraphDatabase.driver(uri, auth=(user, password))

def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return [record for record in result]

@app.route("/")
def index_page():
    try:
        # Query untuk mendapatkan jumlah HamaPadi
        query_hama_padi = "MATCH (n:HamaPadi) RETURN count(n) AS jumlahHamaPadi"
        hama_padi_result = run_query(query_hama_padi)
        jumlah_hama_padi = hama_padi_result[0]["jumlahHamaPadi"]

        # Query untuk mendapatkan jumlah PatogenPadi
        query_patogen_padi = "MATCH (n:PatogenPadi) RETURN count(n) AS jumlahPatogenPadi"
        patogen_padi_result = run_query(query_patogen_padi)
        jumlah_patogen_padi = patogen_padi_result[0]["jumlahPatogenPadi"]

        # Query untuk mendapatkan jumlah PenyakitPadi
        query_penyakit_padi = "MATCH (n:PenyakitPadi) RETURN count(n) AS jumlahPenyakitPadi"
        penyakit_padi_result = run_query(query_penyakit_padi)
        jumlah_penyakit_padi = penyakit_padi_result[0]["jumlahPenyakitPadi"]

        # Query untuk mendapatkan masing-masing satu node dengan label HamaPadi, PatogenPadi, dan PenyakitPadi
        query_hama = "MATCH (h:HamaPadi) WITH h, rand() AS random RETURN h ORDER BY random LIMIT 1"
        query_patogen = "MATCH (p:PatogenPadi) WITH p, rand() AS random RETURN p ORDER BY random LIMIT 1"
        query_penyakit = "MATCH (d:PenyakitPadi) WITH d, rand() AS random RETURN d ORDER BY random LIMIT 1"

        hama_result = run_query(query_hama)
        patogen_result = run_query(query_patogen)
        penyakit_result = run_query(query_penyakit)

        nodes_list = []
        if hama_result:
            nodes_list.append({
                "label": hama_result[0]["h"].get("label", ""),
                "abstract": ' '.join(hama_result[0]["h"].get("abstract", "").split()[:5]) + "..."
            })
        if patogen_result:
            nodes_list.append({
                "label": patogen_result[0]["p"].get("label", ""),
                "abstract": ' '.join(patogen_result[0]["p"].get("abstract", "").split()[:5]) + "..."
            })
        if penyakit_result:
            nodes_list.append({
                "label": penyakit_result[0]["d"].get("label", ""),
                "abstract": ' '.join(penyakit_result[0]["d"].get("abstract", "").split()[:5]) + "..."
            })

        # Logging nodes_list
        logging.debug(f"Formatted nodes list: {nodes_list}")

        return render_template(
            "Landingpage.html",
            # "Backup.html",
            jumlah_hama_padi=jumlah_hama_padi,
            jumlah_patogen_padi=jumlah_patogen_padi,
            jumlah_penyakit_padi=jumlah_penyakit_padi,
            nodes_list=nodes_list
        )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500

@app.route('/diagnosa')
def diagnosa():
    return render_template('Diagnosa.html')

@app.route('/hasildiagnosa')
def hasildiagnosa():
    return render_template('HasilDiagnosa.html')

@app.route('/tipsperawatan')
def tipsperawatan():
    return render_template('tipsperawatan.html')

@app.route("/test-connection", methods=["GET"])
def test_connection():
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return jsonify({"status": "Connection successful"}), 200
    except Exception as e:
        logging.error(f"Connection failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/perpustakaan')
def perpustakaan():
    return render_template('perpustakaan.html')

@app.route('/search-results')
def search_results():
    query = request.args.get('query', '')
    category = request.args.get('category', '')

    try:
        label_filter = ""
        if category == 'penyakit':
            label_filter = "PenyakitPadi"
        elif category == 'hama':
            label_filter = "HamaPadi"
        else:
            label_filter = "PenyakitPadi|HamaPadi"

        if not query or query.lower() == 'random':
            search_query = f"MATCH (n) WHERE ANY(label IN labels(n) WHERE label =~ '{label_filter}') RETURN n ORDER BY rand() LIMIT 10"
        else:
            search_query = f"MATCH (n) WHERE toLower(n.label) CONTAINS toLower($query) AND ANY(label IN labels(n) WHERE label =~ '{label_filter}') RETURN n LIMIT 10"

        nodes = run_query(search_query, {"query": query})

        nodes_list = [
            {
                "abstract": ' '.join(record["n"].get("abstract", "").split()[:5]) + "...",
                "label": record["n"].get("label", ""),
                "Vector": record["n"].get("Vector", []),
                "uri": record["n"].get("uri", "")
            }
            for record in nodes
        ]

        logging.debug(f"Fetched nodes: {nodes_list}")
        return jsonify({"nodes": nodes_list})

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/details')
def details_page():
    label = request.args.get('label', '')

    # Log the received label
    logging.debug(f"Received label: {label}")

    if not label:
        return "Label is required", 400

    try:
        query = """
        MATCH (n {label: $label})
        WITH n, labels(n) AS allLabels
        UNWIND allLabels AS label
        WITH n, CASE 
            WHEN label = "PenyakitPadi" THEN "Penyakit Padi"
            WHEN label = "PatogenPadi" THEN "Patogen Padi"
            WHEN label = "HamaPadi" THEN "Hama Padi"
            WHEN label = "Biologis" THEN "Agen Biologi"
            ELSE label
        END AS modifiedLabel
        WHERE modifiedLabel IN ["Fungisida", "Gejala", "Penyakit Padi", "Patogen Padi", "Hama Padi", "Agen Biologi", "Bakterisida", "Pestisida"]
        WITH n, collect(modifiedLabel) AS labelobjects
        OPTIONAL MATCH (n)-[:memilikiGejala]->(gejala)
        OPTIONAL MATCH (n)-[:diberikanFungisida]->(fungisida)
        OPTIONAL MATCH (n)-[:diberikanBakterisida]->(bakterisida)
        OPTIONAL MATCH (n)-[:diberikanPestisida]->(pestisida)
        OPTIONAL MATCH (n)-[:diberikanAgenBiologi]->(agenbiologi)
        OPTIONAL MATCH (n)-[:terkenaPatogen]->(patogenpadi)
        RETURN n,
            labelobjects,
            collect(DISTINCT {label: gejala.label, abstract: gejala.abstract}) AS gejalaInfo,
            collect(DISTINCT {label: fungisida.label, abstract: fungisida.abstract}) AS fungisidaInfo,
            collect(DISTINCT {label: bakterisida.label, abstract: bakterisida.abstract}) AS bakterisidaInfo,
            collect(DISTINCT {label: pestisida.label, abstract: pestisida.abstract}) AS pestisidaInfo,
            collect(DISTINCT {label: agenbiologi.label, abstract: agenbiologi.abstract}) AS agenbiologiInfo,
            collect(DISTINCT {label: patogenpadi.label, abstract: patogenpadi.abstract}) AS patogenInfo
        """
        result = run_query(query, {"label": label})

        if result:
            node = result[0]['n']
            labels = result[0]['labelobjects']
            gejala_info = result[0]['gejalaInfo']
            fungisida_info = result[0]['fungisidaInfo']
            bakterisida_info = result[0]['bakterisidaInfo']
            pestisida_info = result[0]['pestisidaInfo']
            agenbiologi_info = result[0]['agenbiologiInfo']
            patogen_info = result[0]['patogenInfo']

            logging.debug(f"Node: {node}")
            logging.debug(f"Label Objects: {labels}")
            logging.debug(f"Gejala Info: {gejala_info}")
            logging.debug(f"Fungisida Info: {fungisida_info}")
            logging.debug(f"Bakterisida Info: {bakterisida_info}")
            logging.debug(f"Pestisida Info: {pestisida_info}")
            logging.debug(f"Agen Biologi Info: {agenbiologi_info}")
            logging.debug(f"Patogen Info: {patogen_info}")

            gejala_info_list = [gejala for gejala in gejala_info if gejala.get('label')]
            fungisida_info_list = [fungisida for fungisida in fungisida_info if fungisida.get('label')]
            bakterisida_info_list = [bakterisida for bakterisida in bakterisida_info if bakterisida.get('label')]
            pestisida_info_list = [pestisida for pestisida in pestisida_info if pestisida.get('label')]
            agenbiologi_info_list = [agenbiologi for agenbiologi in agenbiologi_info if agenbiologi.get('label')]
            patogen_info_list = [patogen for patogen in patogen_info if patogen.get('label')]

            logging.debug(f"Gejala Info List: {gejala_info_list}")
            logging.debug(f"Fungisida Info List: {fungisida_info_list}")
            logging.debug(f"Bakterisida Info List: {bakterisida_info_list}")
            logging.debug(f"Pestisida Info List: {pestisida_info_list}")
            logging.debug(f"Agen Biologi Info List: {agenbiologi_info_list}")
            logging.debug(f"Patogen Info List: {patogen_info_list}")

            return render_template(
                "DetailInformation.html",
                label=node.get("label", ""),
                labels=labels,
                abstract=node.get("abstract", ""),
                gejala_info=gejala_info_list,
                fungisida_info=fungisida_info_list,
                bakterisida_info=bakterisida_info_list,
                pestisida_info=pestisida_info_list,
                agenbiologi_info=agenbiologi_info_list,
                patogen_info=patogen_info_list
            )
        else:
            logging.warning(f"No results found for label: {label}")
            return f"No details found for {label}", 404

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500

@app.route('/details-2')
def details2_page():
    label = request.args.get('label', '')

    # Log the received label
    logging.debug(f"Received label: {label}")

    if not label:
        return "Label is required", 400

    try:
        query = """
        MATCH (n {label: $label})
        WITH n, labels(n) AS allLabels
        UNWIND allLabels AS label
        WITH n, CASE 
            WHEN label = "PenyakitPadi" THEN "Penyakit Padi"
            WHEN label = "PatogenPadi" THEN "Patogen Padi"
            WHEN label = "HamaPadi" THEN "Hama Padi"
            WHEN label = "Biologis" THEN "Agen Biologi"
            ELSE label
        END AS modifiedLabel
        WHERE modifiedLabel IN ["Fungisida", "Gejala", "Penyakit Padi", "Patogen Padi", "Hama Padi", "Agen Biologi", "Bakterisida", "Pestisida"]
        RETURN n, modifiedLabel AS labelobject
        """
        result = run_query(query, {"label": label})

        if result:
            node = result[0]['n']
            labels = result[0]['labelobject']

            logging.debug(f"Node: {node}")
            logging.debug(f"Label Object: {labels}")

            return render_template(
                "DetailInformation-2.html",
                label=node.get("label", ""),
                abstract=node.get("abstract", ""),
                labels=labels,
            )
        else:
            logging.warning(f"No results found for label: {label}")
            return f"No details found for {label}", 404

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)
