drop table if exists annotations;
create table annotations (
  id integer primary key autoincrement,
  image varchar,
  x integer,
  y integer,
  width integer,
  height integer,
  label varchar
);

drop table if exists blobs;
create table blobs (
  id integer primary key autoincrement,
  image varchar,
  x integer,
  y integer,
  width integer,
  height integer
);

drop table if exists lines;
create table lines (
  id integer primary key autoincrement,
  bon varchar,
  x integer,
  y integer,
  width integer,
  height integer
);
drop table if exists users;
    create table users (
    id integer primary key autoincrement,
    username text not null,
    email text not null,
    password text not null
);