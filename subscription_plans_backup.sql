--
-- PostgreSQL database dump
--

\restrict k1YkvVAmxcMQ1XztMeGduH2cohjF4OWwXeFW9uXd4eEcQYX509Dkk0ovqZ66m7T

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: subscription_plans; Type: TABLE; Schema: public; Owner: weld_user
--

CREATE TABLE public.subscription_plans (
    id character varying NOT NULL,
    name character varying NOT NULL,
    description character varying,
    monthly_price double precision,
    quarterly_price double precision,
    yearly_price double precision,
    currency character varying,
    max_wps_files integer,
    max_pqr_files integer,
    max_ppqr_files integer,
    max_materials integer,
    max_welders integer,
    max_equipment integer,
    max_factories integer,
    max_employees integer,
    features character varying,
    sort_order integer,
    is_active boolean,
    is_recommended boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.subscription_plans OWNER TO weld_user;

--
-- Data for Name: subscription_plans; Type: TABLE DATA; Schema: public; Owner: weld_user
--

COPY public.subscription_plans (id, name, description, monthly_price, quarterly_price, yearly_price, currency, max_wps_files, max_pqr_files, max_ppqr_files, max_materials, max_welders, max_equipment, max_factories, max_employees, features, sort_order, is_active, is_recommended, created_at, updated_at) FROM stdin;
\.


--
-- Name: subscription_plans subscription_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: weld_user
--

ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict k1YkvVAmxcMQ1XztMeGduH2cohjF4OWwXeFW9uXd4eEcQYX509Dkk0ovqZ66m7T

