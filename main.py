from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile
from slugify import slugify
from sqlalchemy.orm import Session
from passlib.context import CryptContext


from database import Base, get_db, engine
from models import File, Repository, User
from script import create_url_or_api_key, s3
from schemas import FileItem, RepositoryItem, UserAdd, OneRepository


app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
Base.metadata.create_all(engine)


# Routing
@app.get('/')
def main():
    return "main page"


## Auth operations
@app.post("/register")
def register_user(data: UserAdd, db: Session = Depends(get_db)):
    user1 = db.query(User).filter(User.name == data.name).first()
    user2 = db.query(User).filter(User.email == data.email).first()
    if user1 or user2:
        return {"message": "User with this email or username already exists"}
    else:
        hashed_password = pwd_context.hash(data.password)
        user = User(
            email=data.email,
            name=data.name,
            password=hashed_password,
            api_key=create_url_or_api_key(50)
        )
        db.add(user)
        db.commit()

        return {"message": "success", "api_key": user.api_key}


@app.get('/get-api-key')
def whoami(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username and User.password == password).first()

    if not user:
        raise HTTPException(status_code=401, detail="user does not exist")

    is_password_correct = pwd_context.verify(password, user.password)

    if not is_password_correct:
        raise HTTPException(status_code=403, detail="incorrect password or username")

    return user.api_key



## Repositories operations
@app.post('/repositories/create', response_model=RepositoryItem)
def create_repository(api_key: str, name: str, db: Session = Depends(get_db)):
    if db.query(Repository).filter(Repository.view_name == name).first():
        HTTPException(status_code=403, detail="incorrect api key")
    user = db.query(User).filter(User.api_key == api_key).first()
    if user == None:
        raise HTTPException(status_code=403, detail="incorrect api key")

    rep_name = f'filehosting-litix-{slugify(user.name)}-{slugify(name)}'
    s3.create_bucket(Bucket=rep_name)

    rep = Repository(
        view_name=name,
        name=rep_name,
        link=create_url_or_api_key(30),
        user_api_key=api_key
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)

    return rep


@app.get('/repository/all', response_model=list[RepositoryItem])
def repository_list(api_key: str, skip: int = 0, limit: int = 100,db: Session = Depends(get_db)):
    if db.query(User).filter(User.api_key == api_key).first() == None:
        raise HTTPException(status_code=403, detail="incorrect api key")

    if limit < 0:
        raise HTTPException(status_code=404, detail="limit less than 0")

    return db.query(Repository).filter(Repository.user_api_key == api_key).offset(skip).limit(limit).all()


@app.get('/repository/{link}', response_model=OneRepository)
def get_repository(link: str, db: Session = Depends(get_db)):

    repository = db.query(Repository).filter(Repository.link == link).first()
    if repository == None:
        raise HTTPException(status_code=404, detail="repository does not exist")

    files = db.query(File).filter(File.rep_id == repository.id).all()

    return {"name": repository.view_name, "files": files}


@app.delete('/repositories/delete')
def delete_repository(api_key: str, link: str, db: Session = Depends(get_db)):
    rep = db.query(Repository).filter(Repository.link == link).first()

    if rep == None:
        return HTTPException(status_code=404, detail="repository does not exist")

    if rep.user_api_key != api_key:
        raise HTTPException(status_code=403, detail="incorrect api key")


    files = db.query(File).filter(File.rep_id == rep.id)

    files.delete(synchronize_session=False)
    db.delete(rep)
    db.commit()

    try:
        file_list = s3.list_objects(Bucket=rep.name)["Contents"]
        for file in file_list:
            s3.delete_object(Bucket=rep.name, Key=file["Key"])
        s3.delete_bucket(Bucket=rep.name)
    except:
        s3.delete_bucket(Bucket=rep.name)

    return "success"



## File operations
@app.post('/file/add', response_model=FileItem)
def add_file(api_key: str, link: str, file: UploadFile, db: Session = Depends(get_db)):
    rep = db.query(Repository).filter(Repository.link == link).first()

    if rep == None:
        raise HTTPException(status_code=404, detail="repository does not exist")

    if rep.user_api_key != api_key:
        raise HTTPException(status_code=403, detail="incorrect api key")


    file_name = slugify(file.filename)
    url = f'/file/read?link={rep.link}&name={file.filename}'

    s3.upload_fileobj(file.file, Bucket=rep.name, Key=file.filename)
    newfile = File(
        view_name=file.filename,
        name=file_name,
        download_link=url,
        rep_id=rep.id
    )
    db.add(newfile)
    db.commit()

    return newfile


@app.delete('/file/remove')
def remove_file(api_key: str, bucket_name: str, name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key == api_key).first()

    if user == None:
        raise HTTPException(status_code=403, detail="incorrect api key")

    bucket = f"filehosting-litix-{user.name}-{bucket_name}"
    rep = db.query(Repository).filter(Repository.name == bucket).first()
    file = db.query(File).filter(File.view_name == name)

    if rep == None:
        raise HTTPException(status_code=404, detail="repository does not exist")

    if file.first() == None:
        raise HTTPException(status_code=404, detail="file does not exist")

    s3.delete_object(Bucket=bucket, Key=name)
    file = file
    file.delete()
    db.commit()

    return "success"


@app.get('/file/read')
def download_file(link: str, name: str, db: Session = Depends(get_db)):
    file_name = db.query(File).filter(File.view_name == name).first()
    bucket = db.query(Repository).filter(Repository.link == link).first()

    if file_name == None:
        raise HTTPException(status_code=404, detail="file does not exist")

    if bucket == None:
        raise HTTPException(status_code=404, detail="repository does not exist")

    content = s3.get_object(Bucket=bucket.name, Key=file_name.view_name)['Body'].read()

    return Response(
        content=content,
        headers={
            'Content-Disposition': f'attachment;filename={file_name.view_name}',
            'Content-Type': 'application/octet-stream',
            'Access-Control-Expose-Headers': 'Content-Disposition',
        }
    )