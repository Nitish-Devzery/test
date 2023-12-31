import logging
import os

import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.orm import aliased
from sqlalchemy import func, text, desc, TIMESTAMP
import threading

from app import get_test_case_details

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
aimodel_base_url = os.getenv('AIMODEL_BASE_URL')
tc_base_url = os.getenv('TESTCASE_GENERATION_BASE_URL')
bubble_wf_url = os.getenv('BUBBLE_WF_URL')
bubble_data_url = os.getenv('BUBBLE_DATA_URL')
targetted_reg_url=os.getenv('TARGETTED_REG_URL')
CORS(app)


logging.basicConfig(
    level=logging.DEBUG,  # Set your desired log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log message format
)

db = SQLAlchemy(app)

session = db.session

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    testcasesleft = db.Column(db.Integer)
    added_at = db.Column(TIMESTAMP, server_default=func.now(), nullable=False)
    feedback_displayed = db.Column(db.Boolean)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'organization': self.organization,
            'industry': self.industry,
            # 'role_id': self.role_id,
            # 'plan_id': self.plan_id,
            'testcasesleft': self.testcasesleft,
            'company_role': self.company_role,
            'workspace_name': self.workspace_name,
            'company_domain': self.company_domain,
            'team_size': self.team_size,
            'whitelisted': self.whitelisted,
            'demo': self.demo,
            'subscribed': self.subscribed,
            'added_at': self.added_at,
            'feedback_displayed': self.feedback_displayed
        }





class ProductRequirements(db.Model):
    __tablename__ = 'productrequirements'
    id = db.Column(db.Integer, primary_key=True)
    document = db.Column(db.Text, nullable=False)
    codesnippet = db.Column(db.Text, nullable=False)
    htmlcode_id = db.Column(db.Integer, db.ForeignKey('htmlcodes.id'))

    def serialize(self):
        return {
            'id': self.id,
            'document': self.document,
            'codesnippet': self.codesnippet,
            'htmlcode_id': self.htmlcode_id
        }


class HtmlCodes(db.Model):
    __tablename__ = 'htmlcodes'
    id = db.Column(db.Integer, primary_key=True)
    htmlcode = db.Column(db.String, nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'))

    def serialize(self):
        return {
            'id': self.id,
            'htmlcode': self.htmlcode,
            'module_id': self.module_id
        }



class Modules(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    modulenumber = db.Column(db.Integer, nullable=False)
    modulename = db.Column(db.String(255), nullable=False)
    added_at = db.Column(TIMESTAMP, server_default=func.now(), nullable=False)
    productversion_id = db.Column(db.Integer, db.ForeignKey('versions.id'))

    def serialize(self):
        return {
            'id': self.id,
            'modulenumber': self.modulenumber,
            'modulename': self.modulename,
            'productversion_id': self.productversion_id
        }


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    answer1 = db.Column(db.Text)
    answer2 = db.Column(db.Text)
    answer3 = db.Column(db.Text)
    answer4 = db.Column(db.Text)
    type = db.Column(db.Text)
    chatsummary = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def serialize(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'answer1': self.answer1,
            'answer2': self.answer2,
            'answer3': self.answer3,
            'answer4': self.answer4,
            'type': self.type,
            'chatsummary': self.chatsummary
            # Add other columns if needed for serialization
        }

class Scenarios(db.Model):
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    scenarionumber = db.Column(db.Integer, nullable=False)
    scenarioname = db.Column(db.String(255), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'))

    def serialize(self):
        return {
            'id': self.id,
            'scenarionumber': self.scenarionumber,
            'scenarioname': self.scenarioname,
            'module_id': self.module_id
        }


class TestCases(db.Model):
    __tablename__ = 'testcases'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    testcasenumber = db.Column(db.Integer, nullable=False)
    testcasename = db.Column(db.String(255), nullable=False)
    testcasedetails = db.Column(db.String(255))
    priority = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Boolean, nullable=True, default=None)
    steps = db.Column(db.Text)
    expectedresults = db.Column(db.Text)
    screenshoturl = db.Column(db.Text)  # New column for screenshot URL
    attachmentlink = db.Column(db.Text)  # New column for attachment link
    scenario_id = db.Column(db.Integer)
    failure_probability = db.Column(db.DECIMAL(precision=16, scale=8))

    def serialize(self):
        return {
            'id': self.id,
            'testcasenumber': self.testcasenumber,
            'testcasename': self.testcasename,
            'testcasedetails': self.testcasedetails,
            'priority': self.priority,
            'severity': self.severity,
            'status': self.status,
            'steps': self.steps,
            'expectedresults': self.expectedresults,
            'screenshoturl': self.screenshoturl,  # Include the new columns
            'attachmentlink': self.attachmentlink,  # Include the new columns
            'scenario_id': self.scenario_id,
            'failure_probability': self.failure_probability
        }

class TestCases_Temp(db.Model):
    __tablename__ = 'testcases_temporary'
    id = db.Column(db.Integer, primary_key=True)
    testcasename = db.Column(db.String(255), nullable=False)
    testcasedetails = db.Column(db.String(255))
    priority = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Boolean, nullable=True, default=None)
    steps = db.Column(db.Text)
    expectedresults = db.Column(db.Text)
    screenshoturl = db.Column(db.Text)  # New column for screenshot URL
    attachmentlink = db.Column(db.Text)  # New column for attachment link
    scenario_id = db.Column(db.Integer)

    def serialize(self):
        return {
            'id': self.id,
            'testcasename': self.testcasename,
            'testcasedetails': self.testcasedetails,
            'priority': self.priority,
            'severity': self.severity,
            'status': self.status,
            'steps': self.steps,
            'expectedresults': self.expectedresults,
            'screenshoturl': self.screenshoturl,  # Include the new columns
            'attachmentlink': self.attachmentlink,  # Include the new columns
            'scenario_id': self.scenario_id
        }


class TestCasesHistory(db.Model):
    __tablename__ = 'testcaseshistory'
    id = db.Column(db.Integer, primary_key=True)
    testcasenumber = db.Column(db.Integer, nullable=False)
    testcasename = db.Column(db.String(255), nullable=False)
    testcasedetails = db.Column(db.String(255))
    priority = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Boolean, nullable=True, default=None)
    steps = db.Column(db.Text)
    expectedresults = db.Column(db.Text)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'))
    parent_testcase_id = db.Column(db.Integer, db.ForeignKey('testcases.id')) # Self-referencing foreign key
    failure_probability = db.Column(db.DECIMAL(precision=16, scale=8))

    def serialize(self):
        return {
            'id': self.id,
            'testcasenumber': self.testcasenumber,
            'testcasename': self.testcasename,
            'testcasedetails': self.testcasedetails,
            'priority': self.priority,
            'severity': self.severity,
            'status': self.status,
            'steps': self.steps,
            'expectedresults': self.expectedresults,
            'scenario_id': self.scenario_id,
            'parent_testcase_id': self.parent_testcase_id,
            'failure_probability': self.failure_probability
        }

class Bugs(db.Model):
    __tablename__ = 'bugs'
    id = db.Column(db.Integer, primary_key=True)
    testcasenumber = db.Column(db.Integer, nullable=False)
    testcasename = db.Column(db.String(255), nullable=False)
    testcasedetails = db.Column(db.String(255))
    priority = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Boolean, nullable=True, default=None)
    steps = db.Column(db.Text)
    expectedresults = db.Column(db.Text)
    screenshoturl = db.Column(db.Text)  # New column for screenshot URL
    attachmentlink = db.Column(db.Text)  # New column for attachment link
    module_id = db.Column(db.Integer)
    testcases_id = db.Column(db.Integer)
    bugnumber = db.Column(db.Integer)
    jiraselfurl = db.Column(db.Text)

    def serialize(self):
        return {
            'id': self.id,
            'testcasenumber': self.testcasenumber,
            'testcasename': self.testcasename,
            'testcasedetails': self.testcasedetails,
            'priority': self.priority,
            'severity': self.severity,
            'status': self.status,
            'steps': self.steps,
            'expectedresults': self.expectedresults,
            'screenshoturl': self.screenshoturl,  # Include the new columns
            'attachmentlink': self.attachmentlink,  # Include the new columns
            'testcases_id': self.testcases_id,
            'module_id' : self.module_id,
            'bugnumber': self.bugnumber,
            'jiraselfurl': self.jiraselfurl
        }


class Versions(db.Model):
    __tablename__ = 'versions'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    version_name = db.Column(db.String(255), nullable=False)
    changes = db.Column(db.Text)

    def serialize(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'version_name': self.version_name,
            'changes': self.changes
        }


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    feedback_text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users', backref=db.backref('feedback', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'user_id': self.user_id,
            'user': self.user.serialize() if self.user else None
        }



with app.app_context():

    @app.route('/ospi/html/<int:version_id>', methods=['GET'])
    def html_retrieve(version_id):
        print('Retrieve html triggered!')

        versions = HtmlCodes.query.filter_by(version_id=version_id).all()

        return jsonify([version.serialize() for version in versions]),200


    @app.route('/ospi/users/<int:user_id>/products', methods=['GET'])
    def get_products_for_user(user_id):
        products = Products.query.filter_by(user_id=user_id).all()
        db.session.remove()
        # print(products)
        return jsonify([product.serialize() for product in products])


    @app.route('/ospi/users/<int:user_id>/products_withversion', methods=['GET'])
    def get_products_for_user_with_version(user_id):
        # Subquery to get the latest version_id for each product
        # Subquery to get the latest version_id and version_name for each product
        latest_version_subquery = (
            db.session.query(
                Versions.product_id,
                func.max(Versions.id).label('latest_version_id'),
                func.max(Versions.version_name).label('latest_version_name')
            )
            .group_by(Versions.product_id)
            .subquery()
        )

        # Query to get products, latest version_id, and latest version_name
        products = (
            db.session.query(
                Products,
                latest_version_subquery.c.latest_version_id,
                latest_version_subquery.c.latest_version_name
            )
            .filter(Products.user_id == user_id)
            .outerjoin(latest_version_subquery, Products.id == latest_version_subquery.c.product_id)
            .all()
        )

        db.session.remove()

        # Serialize the products, latest_version_id, and latest_version_name
        product_data = [
            {
                'product_info': product[0].serialize(),
                'latest_version_id': product[1],
                'latest_version_name': product[2]
            }
            for product in products
        ]

        return jsonify(product_data)


    @app.route('/ospi/testcases/update', methods=['POST'])
    def update_testcases():
        data = request.get_json()
        app.logger.info(data)
        updated_test_cases = data.get('testCases')
        print('updated test cases' , updated_test_cases)

        for updated_test_case in updated_test_cases:
            test_case_id = updated_test_case.get('id')
            test_case = TestCases.query.get(test_case_id)

            if test_case:
                test_case.testCase = updated_test_case.get('testCase')
                test_case.priority = updated_test_case.get('priority')
                test_case.severity = updated_test_case.get('severity')
                test_case.status = updated_test_case.get('status')

        db.session.commit()

        # Return the updated test cases if necessary
        return jsonify(updated_test_cases),200


    @app.route('/ospi/testcases/updateinduvidual', methods=['POST'])
    def update_testcase_individually():
        try:
            data = request.get_json()
        #     logging.info(data)
            test_case_id = data.get('id')
            # test_case_id = 54952
            logging.info(test_case_id)
            # print(test_case_id)
            test_case = session.get(TestCases,test_case_id)
            # print(test_case)

            description = data.get('description', None)
            logging.info(test_case)
            status = data.get('status')
            # status = 'Pass'
            print(status)
            if status == 'Pass':
                status = True
            elif status == 'Fail':
                status= False
            else:
                status = None
            # app.logger.info(status)
            if test_case:
                test_case.testcasename = data.get('testcasename')
                test_case.priority = data.get('priority')
                test_case.severity = data.get('severity')
                test_case.status = status
                test_case.testcasedetails = description

                db.session.commit()
                updated_test_case = session.get(TestCases, test_case_id)

                if updated_test_case:
                    # Create a dictionary containing the updated test case data
                    updated_test_case_data = {
                        'id': updated_test_case.id,
                        'testcasename': updated_test_case.testcasename,
                        'priority': updated_test_case.priority,
                        'severity': updated_test_case.severity,
                        'status': updated_test_case.status
                    }

                    # Return the updated test case data along with the success message
                    return jsonify(
                        {'message': 'Test case updated successfully', 'test_case': updated_test_case_data}), 200
                else:
                    return jsonify({'message': 'Failed to retrieve updated test case'}), 500
            else:
                return jsonify({'message': 'Test case not found'}), 404

        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred', 'error': str(e)}), 500


    @app.route('/ospi/addHTML', methods=['POST'])
    def add_html():
        print('Add html triggered!')
        data = request.json

        # Extract data from the request
        html_content = data.get('html_content')
        module_id = data.get('module_id')

        # Create a new Prds object
        new_html = HtmlCodes(
            htmlcode = html_content,
            module_id = module_id
        )

        # Add the new PRD to the database
        db.session.add(new_html)
        db.session.commit()
        return jsonify({'html_id': new_html.id, 'message': 'HTML added successfully.'}), 200


    def add_history(mapper, connection, target):
        # Get the current version number
        last_history = TestCasesHistory.query.filter_by(testcase_id=target.id).order_by(
            TestCasesHistory.version.desc()).first()
        new_version = 1 if not last_history else last_history.version + 1

        # Create a new history row with the old data
        history = TestCasesHistory(
            testcase=target.testcase,
            priority=target.priority,
            severity=target.severity,
            requirementid=target.requirementid,
            status=target.status,
            version=new_version,
            testcase_id=target.id,
        )

        db.session.add(history)


    @app.route('/ospi/addVersion', methods=['POST'])
    def add_version():

        data = request.get_json()
        print("DB ADD Version: ", data)
        new_version = Versions(
            product_id = data.get('productId'),
            version_name =  data.get('version_name'),
            changes =  data.get('changes')
        )

        db.session.add(new_version)
        db.session.commit()

        return jsonify({"message": "OK", "version_id": new_version.id}), 200


    @app.route('/ospi/products/versions/<int:version_id>', methods=['GET'])
    def get_chat_summary_for_version(version_id):
        version = Versions.query.filter_by(id=version_id).first()
        if version is not None:
            product = Products.query.filter_by(id=version.product_id).first()
            if product is not None:
                print('Chat summary found:', product.chatsummary)
                return jsonify({'chatsummary': product.chatsummary}), 200
            else:
                print('Product not found for the version')
                return jsonify({'message': 'Product not found for the version'}), 400
        else:
            print('Version not found')
            return jsonify({'message': 'Version not found'}), 400


    @app.route('/ospi/testcasesbulk', methods=['POST'])
    def add_test_cases_bulk():

        try:
            data = request.json
            print(data)
            # List to hold all new TestCases objects
            new_test_cases = []
            module_id = data[0].get('module_id')
            print("Module ID", module_id)
            result = (
                session.query(Products.id.label('product_id'))
                .join(Versions, Products.id == Versions.product_id)
                .join(Modules, Versions.id == Modules.productversion_id)
                .filter(Modules.id == module_id)
                .first()
            )

            product_id = result.product_id

            # Process all rows in the data array
            for row in data:
                # Extract data from the row
                testcase = row.get('testcasename')
                priority = row.get('priority')
                severity = row.get('severity')
                scenario_id = row.get('scenario_id')
                status = row.get('status')
                testcasedetails = row.get('testcasedetails')
                module_id = row.get('module_id')  # Add module_id to each row


                # Check if a TestCases entry with the same name exists in the same module
                existing_test_case = (
                    db.session.query(TestCases)
                    .join(Scenarios, Scenarios.id == TestCases.scenario_id)
                    .join(Modules, Modules.id == Scenarios.module_id)
                    .filter(Modules.id == module_id, TestCases.testcasename == testcase)
                    .first()
                )

                if existing_test_case:
                    # Skip this row and move on to the next one
                    continue

                # Create a new TestCases object
                new_test_case = TestCases(
                    testcasename=testcase,
                    priority=priority,
                    severity=severity,
                    scenario_id=scenario_id,
                    testcasedetails=testcasedetails,
                    status=status
                )

                # Add the new test case to the list
                new_test_cases.append(new_test_case)

            new_tc_failure =[]
            a = []
            logging.info("New cases")
            for case in new_test_cases:
                case_dict = {
                    "testcasename": case.testcasename,
                    "priority": case.priority,
                    "severity": case.severity,
                    "scenario_id": case.scenario_id,
                    "testcasedetails": case.testcasedetails,
                    "status": case.status
                }

                # print(case_dict)

                # Send the dictionary as JSON in the request
                response = requests.post(f'{targetted_reg_url}/ospi/products/one/{product_id}/versions', json=case_dict)


                case = response.json()
                new_tc_failure.append(case)
            if new_tc_failure:
                print(new_tc_failure)
                test_cases_list =[]
                for case_list in new_tc_failure:
                    for case_data in case_list:
                        new_test_case = TestCases(
                            testcasename=case_data.get('testcasename', ''),
                            priority=case_data.get('priority', ''),
                            severity=case_data.get('severity', ''),
                            scenario_id=case_data.get('scenario_id', ''),
                            testcasedetails=case_data.get('testcasedetails', ''),
                            status=case_data.get('status', ''),
                            failure_probability=case_data.get('failure_probability', '')
                        )

                        test_cases_list.append(new_test_case)

                db.session.add_all(test_cases_list)
                db.session.commit()  # This will persist the new_test_case and assign it an ID

                for new_test_case in test_cases_list:
                    print(f'TestCase ID: {new_test_case.id}, TestCasename: {new_test_case.testcasename}')
                # Access the ID after commit


                    print(case_data)


                    all_details = get_test_case_details(new_test_case.id)

                    a.append(all_details)


                    # Join the details with newline characters
                data = "\n".join(a)
                print(data)

                url = f'{bubble_data_url}/bulk'
                headers = {'Content-Type': 'text/plain'}

                # Send the data in one bulk request
                response = requests.post(url, data=data, headers=headers)

                print(response.text)

                return jsonify({"message": "Added testcases"}), 200
            else:
                return jsonify({"message": "No new testcases to add"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400


