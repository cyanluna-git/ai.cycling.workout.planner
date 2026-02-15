


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


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."get_week_end"("check_date" "date" DEFAULT CURRENT_DATE) RETURNS "date"
    LANGUAGE "plpgsql" IMMUTABLE
    AS $$
BEGIN
    RETURN get_week_start(check_date) + 6;
END;
$$;


ALTER FUNCTION "public"."get_week_end"("check_date" "date") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_week_start"("check_date" "date" DEFAULT CURRENT_DATE) RETURNS "date"
    LANGUAGE "plpgsql" IMMUTABLE
    AS $$
BEGIN
    -- ISO week starts on Monday
    RETURN check_date - EXTRACT(ISODOW FROM check_date)::INTEGER + 1;
END;
$$;


ALTER FUNCTION "public"."get_week_start"("check_date" "date") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  INSERT INTO public.user_settings (user_id)
  VALUES (new.id);
  
  INSERT INTO public.user_api_keys (user_id)
  VALUES (new.id);
  
  RETURN new;
END;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."api_request_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "method" "text" NOT NULL,
    "path" "text" NOT NULL,
    "status_code" integer,
    "response_time_ms" integer,
    "ip_address" "text",
    "user_agent" "text",
    "request_body" "jsonb",
    "error_message" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."api_request_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "event_type" "text" NOT NULL,
    "user_id" "uuid",
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "ip_address" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."audit_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."daily_workouts" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "plan_id" "uuid",
    "user_id" "uuid" NOT NULL,
    "workout_date" "date" NOT NULL,
    "planned_name" character varying(255),
    "planned_type" character varying(50),
    "planned_duration" integer,
    "planned_tss" integer,
    "planned_description" "text",
    "planned_steps" "jsonb",
    "planned_modules" "jsonb",
    "planned_rationale" "text",
    "planned_at" timestamp with time zone DEFAULT "now"(),
    "actual_name" character varying(255),
    "actual_type" character varying(50),
    "actual_duration" integer,
    "actual_tss" integer,
    "actual_description" "text",
    "actual_steps" "jsonb",
    "actual_modules" "jsonb",
    "actual_generated_at" timestamp with time zone,
    "regeneration_reason" "text",
    "status" character varying(20) DEFAULT 'planned'::character varying,
    "intervals_event_id" integer,
    "completed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "session" "text",
    "customization" "jsonb",
    "profile_id" integer,
    "actual_design_goal" "text",
    "actual_coaching" "jsonb"
);


ALTER TABLE "public"."daily_workouts" OWNER TO "postgres";


COMMENT ON TABLE "public"."daily_workouts" IS 'Individual daily workouts within weekly plans';



CREATE TABLE IF NOT EXISTS "public"."job_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "job_type" character varying(50) NOT NULL,
    "user_id" "uuid" NOT NULL,
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "priority" integer DEFAULT 0,
    "payload" "jsonb",
    "scheduled_at" timestamp with time zone NOT NULL,
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "retry_count" integer DEFAULT 0,
    "max_retries" integer DEFAULT 3,
    "error_message" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."job_queue" OWNER TO "postgres";


COMMENT ON TABLE "public"."job_queue" IS 'Background job queue for async processing';



CREATE TABLE IF NOT EXISTS "public"."llm_models" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "provider" "text" NOT NULL,
    "model_id" "text" NOT NULL,
    "display_name" "text",
    "is_active" boolean DEFAULT true,
    "priority" integer DEFAULT 0,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."llm_models" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."saved_workouts" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "workout_date" "date" NOT NULL,
    "workout_type" "text",
    "design_goal" "text",
    "workout_text" "text" NOT NULL,
    "estimated_tss" integer,
    "duration_minutes" integer,
    "intervals_event_id" bigint,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "steps_json" "text",
    "zwo_content" "text"
);


ALTER TABLE "public"."saved_workouts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_api_keys" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "intervals_api_key" "text",
    "athlete_id" "text",
    "llm_provider" "text" DEFAULT 'gemini'::"text",
    "llm_api_key" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_api_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_settings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "ftp" integer DEFAULT 200,
    "max_hr" integer DEFAULT 190,
    "lthr" integer DEFAULT 170,
    "training_goal" "text" DEFAULT '지구력 강화'::"text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_admin" boolean DEFAULT false,
    "exclude_barcode_workouts" boolean DEFAULT false NOT NULL,
    "training_style" character varying(50) DEFAULT 'auto'::character varying,
    "preferred_duration" integer DEFAULT 60,
    "weekly_plan_enabled" boolean DEFAULT false,
    "weekly_plan_day" integer DEFAULT 0,
    "training_focus" character varying(20) DEFAULT 'maintain'::character varying,
    "weekly_tss_target" integer,
    "weekly_availability" "jsonb" DEFAULT '{"0": "available", "1": "available", "2": "available", "3": "available", "4": "available", "5": "available", "6": "available"}'::"jsonb"
);


ALTER TABLE "public"."user_settings" OWNER TO "postgres";


COMMENT ON COLUMN "public"."user_settings"."exclude_barcode_workouts" IS 'Exclude barcode-style interval workouts (40/20, 30/30, etc.) from generation. Recommended for ERG trainers with slow power response.';



COMMENT ON COLUMN "public"."user_settings"."training_style" IS 'Training philosophy: auto, polarized, norwegian, sweetspot, threshold, endurance';



COMMENT ON COLUMN "public"."user_settings"."preferred_duration" IS 'Preferred workout duration in minutes';



COMMENT ON COLUMN "public"."user_settings"."weekly_plan_enabled" IS 'Enable automatic weekly workout plan generation';



COMMENT ON COLUMN "public"."user_settings"."weekly_plan_day" IS 'Day to generate weekly plan (0=Sunday, 1=Monday, ...)';



COMMENT ON COLUMN "public"."user_settings"."weekly_availability" IS '요일별 운동 가능 여부 (0=Mon, 6=Sun): available | unavailable | rest';



CREATE TABLE IF NOT EXISTS "public"."weekly_plans" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "week_start" "date" NOT NULL,
    "week_end" "date" NOT NULL,
    "status" character varying(20) DEFAULT 'active'::character varying,
    "total_planned_tss" integer,
    "training_style" character varying(50),
    "generation_prompt" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "weekly_tss_target" integer,
    "total_actual_tss" integer,
    "achievement_status" character varying(20) DEFAULT NULL::character varying
);


ALTER TABLE "public"."weekly_plans" OWNER TO "postgres";


COMMENT ON TABLE "public"."weekly_plans" IS 'Weekly workout plans generated automatically or manually';



ALTER TABLE ONLY "public"."api_request_logs"
    ADD CONSTRAINT "api_request_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."daily_workouts"
    ADD CONSTRAINT "daily_workouts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."daily_workouts"
    ADD CONSTRAINT "daily_workouts_user_id_date_session_key" UNIQUE ("user_id", "workout_date", "session");



ALTER TABLE ONLY "public"."job_queue"
    ADD CONSTRAINT "job_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."llm_models"
    ADD CONSTRAINT "llm_models_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."saved_workouts"
    ADD CONSTRAINT "saved_workouts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."saved_workouts"
    ADD CONSTRAINT "saved_workouts_user_id_workout_date_key" UNIQUE ("user_id", "workout_date");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."user_settings"
    ADD CONSTRAINT "user_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_settings"
    ADD CONSTRAINT "user_settings_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."weekly_plans"
    ADD CONSTRAINT "weekly_plans_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."weekly_plans"
    ADD CONSTRAINT "weekly_plans_user_id_week_start_key" UNIQUE ("user_id", "week_start");



CREATE INDEX "idx_api_logs_created_at" ON "public"."api_request_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_api_logs_path" ON "public"."api_request_logs" USING "btree" ("path");



CREATE INDEX "idx_api_logs_user_id" ON "public"."api_request_logs" USING "btree" ("user_id");



CREATE INDEX "idx_audit_logs_created_at" ON "public"."audit_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_audit_logs_event_type" ON "public"."audit_logs" USING "btree" ("event_type");



CREATE INDEX "idx_audit_logs_user_id" ON "public"."audit_logs" USING "btree" ("user_id");



CREATE INDEX "idx_daily_workouts_plan" ON "public"."daily_workouts" USING "btree" ("plan_id");



CREATE INDEX "idx_daily_workouts_status" ON "public"."daily_workouts" USING "btree" ("status");



CREATE INDEX "idx_daily_workouts_user_date" ON "public"."daily_workouts" USING "btree" ("user_id", "workout_date");



CREATE INDEX "idx_job_queue_status_scheduled" ON "public"."job_queue" USING "btree" ("status", "scheduled_at");



CREATE INDEX "idx_job_queue_user" ON "public"."job_queue" USING "btree" ("user_id");



CREATE INDEX "idx_weekly_plans_status" ON "public"."weekly_plans" USING "btree" ("status");



CREATE INDEX "idx_weekly_plans_user_week" ON "public"."weekly_plans" USING "btree" ("user_id", "week_start");



CREATE OR REPLACE TRIGGER "update_daily_workouts_updated_at" BEFORE UPDATE ON "public"."daily_workouts" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_weekly_plans_updated_at" BEFORE UPDATE ON "public"."weekly_plans" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "public"."api_request_logs"
    ADD CONSTRAINT "api_request_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."daily_workouts"
    ADD CONSTRAINT "daily_workouts_plan_id_fkey" FOREIGN KEY ("plan_id") REFERENCES "public"."weekly_plans"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."daily_workouts"
    ADD CONSTRAINT "daily_workouts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."job_queue"
    ADD CONSTRAINT "job_queue_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."saved_workouts"
    ADD CONSTRAINT "saved_workouts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_settings"
    ADD CONSTRAINT "user_settings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."weekly_plans"
    ADD CONSTRAINT "weekly_plans_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Authenticated users can read llm_models" ON "public"."llm_models" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Service role can manage llm_models" ON "public"."llm_models" USING (("auth"."role"() = 'service_role'::"text"));



CREATE POLICY "Service role full access to job_queue" ON "public"."job_queue" USING ((("auth"."jwt"() ->> 'role'::"text") = 'service_role'::"text"));



CREATE POLICY "Service role only" ON "public"."audit_logs" USING (("auth"."role"() = 'service_role'::"text"));



CREATE POLICY "Users can delete own daily workouts" ON "public"."daily_workouts" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete own weekly plans" ON "public"."weekly_plans" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own api keys" ON "public"."user_api_keys" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own daily workouts" ON "public"."daily_workouts" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own settings" ON "public"."user_settings" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own weekly plans" ON "public"."weekly_plans" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own workouts" ON "public"."saved_workouts" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own api keys" ON "public"."user_api_keys" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own daily workouts" ON "public"."daily_workouts" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own settings" ON "public"."user_settings" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own weekly plans" ON "public"."weekly_plans" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own workouts" ON "public"."saved_workouts" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own api keys" ON "public"."user_api_keys" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own daily workouts" ON "public"."daily_workouts" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own settings" ON "public"."user_settings" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own weekly plans" ON "public"."weekly_plans" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own workouts" ON "public"."saved_workouts" FOR SELECT USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."api_request_logs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."audit_logs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."daily_workouts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."job_queue" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."llm_models" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."saved_workouts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_api_keys" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_settings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."weekly_plans" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."get_week_end"("check_date" "date") TO "anon";
GRANT ALL ON FUNCTION "public"."get_week_end"("check_date" "date") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_week_end"("check_date" "date") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_week_start"("check_date" "date") TO "anon";
GRANT ALL ON FUNCTION "public"."get_week_start"("check_date" "date") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_week_start"("check_date" "date") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";


















GRANT ALL ON TABLE "public"."api_request_logs" TO "anon";
GRANT ALL ON TABLE "public"."api_request_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."api_request_logs" TO "service_role";



GRANT ALL ON TABLE "public"."audit_logs" TO "anon";
GRANT ALL ON TABLE "public"."audit_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_logs" TO "service_role";



GRANT ALL ON TABLE "public"."daily_workouts" TO "anon";
GRANT ALL ON TABLE "public"."daily_workouts" TO "authenticated";
GRANT ALL ON TABLE "public"."daily_workouts" TO "service_role";



GRANT ALL ON TABLE "public"."job_queue" TO "anon";
GRANT ALL ON TABLE "public"."job_queue" TO "authenticated";
GRANT ALL ON TABLE "public"."job_queue" TO "service_role";



GRANT ALL ON TABLE "public"."llm_models" TO "anon";
GRANT ALL ON TABLE "public"."llm_models" TO "authenticated";
GRANT ALL ON TABLE "public"."llm_models" TO "service_role";



GRANT ALL ON TABLE "public"."saved_workouts" TO "anon";
GRANT ALL ON TABLE "public"."saved_workouts" TO "authenticated";
GRANT ALL ON TABLE "public"."saved_workouts" TO "service_role";



GRANT ALL ON TABLE "public"."user_api_keys" TO "anon";
GRANT ALL ON TABLE "public"."user_api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."user_api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."user_settings" TO "anon";
GRANT ALL ON TABLE "public"."user_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."user_settings" TO "service_role";



GRANT ALL ON TABLE "public"."weekly_plans" TO "anon";
GRANT ALL ON TABLE "public"."weekly_plans" TO "authenticated";
GRANT ALL ON TABLE "public"."weekly_plans" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































drop extension if exists "pg_net";

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


