from flask import Flask, request, abort, render_template, url_for, redirect, flash
import mysql.connector



db_conn = mysql.connector.connect(
    host = 'localhost',
    user = 'pyadmin',
    password = 'qzq',
    database = 'jzon_serv'
)

qurzor = db_conn.cursor()

app = Flask(__name__)
app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def homepage():
    return render_template('index.html')


# get all database records
@app.route('/cars', methods=['GET'])
def get_cars():
    query = qurzor.execute('select * from carz')
    rezult = qurzor.fetchall()
    
    return render_template('cars.html', carz = rezult)


# get single record from ID using prepared statement
@app.route('/cars/<cid>')
def get_car(cid):
    car_id = (cid,)
    qurzor.execute('select * from carz where id = %s', car_id)
    rezult = qurzor.fetchone()

    return render_template('new_car_table.html', car = rezult)


@app.route('/new_car')
def new_car():
     return render_template('new_car_form.html')


@app.route('/new_car_form', methods=['POST'])
def new_car_form():
    brand = request.form['brand']
    model = request.form['model']
    year = request.form["year"]
    convertible = request.form['convertible']

    # get the last inserted ID and the next auto-increment ID, to ensure the next car record will have an id value of last_id + 1, otherwise use a separate sql query to specify the ID, to provide ID continuity
    qurzor.execute('select id from carz order by id desc limit 1')
    last_ID = qurzor.fetchone()
    last_ID = last_ID[0]

    qurzor.execute('select auto_increment from information_schema.tables where table_schema = "jzon_serv" and table_name = "carz"')
    next_ID = qurzor.fetchone()
    next_ID = next_ID[0]

    if next_ID - last_ID != 1:
        next_ID = last_ID + 1
        query = 'insert into carz values (%s, %s, %s, %s, %s)'
        post_value = (next_ID, brand, model, year, convertible)
    else:
        query = 'insert into carz (brand, model, production_year, convertible) values (%s, %s, %s, %s)'
        post_value = (brand, model, year, convertible)

    # insert new record
    qurzor.execute(query, post_value)
    db_conn.commit()
    cid = str(qurzor.lastrowid)
    flash('Car record created successfully!')

    return redirect('/cars/' + cid)


# show form for car update
@app.route('/update_car')
def update_db():
    # get all records to refresh row count, needed for the update_car_form
    qurzor.execute('select * from carz')
    rezult = qurzor.fetchall()
    return render_template('update_car.html', rowz = qurzor.rowcount)
    

# update car record by ID & show the result
# no need for ID validation as the consecutivity is enforced by new_car_form
@app.route('/update_car_form', methods=['POST'])
def update_db_form():

    cid = request.form['id'] 
    brand = request.form['brand']
    model = request.form['model']
    year = request.form['year']
    convertible = request.form['convertible']

    query = 'update carz set brand = %s, model = %s, production_year = %s, convertible = %s where id = %s'
    put_value = (brand, model, year, convertible, cid)
    qurzor.execute(query, put_value)
    db_conn.commit()
    flash('Car record updated uccessfully!')

    return redirect('/cars/'+ cid)



# show form for car delete
@app.route('/delete_car')
def delete_car():
    qurzor.execute('select * from carz')
    rezult = qurzor.fetchall()
    return render_template('delete_car.html', rowz = qurzor.rowcount)


# handle car delete
@app.route('/delete_car_form', methods = ['POST'])
def delete_car_form():
    cid = request.form['id']
    id_query = 'select id from carz where id = %s'
    qurzor.execute(id_query, (cid,))
    id_check = qurzor.fetchone()

    if id_check:
        query = 'delete from carz where id = %s'
        qurzor.execute(query, (cid,))
        db_conn.commit()
        flash('Car record deleted successfully!')

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
