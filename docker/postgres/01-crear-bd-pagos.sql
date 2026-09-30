-- Database-per-service: el microservicio de pagos no comparte esquema con el
-- monolito. Ambos usan el mismo servidor PostgreSQL por simplicidad del taller,
-- pero cada uno es dueno exclusivo de su base de datos.
CREATE DATABASE meetu2_pagos;
