-- 회원 관련 인덱스
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- 채용공고 관련 인덱스
CREATE INDEX idx_job_postings_title ON job_postings(title);
CREATE INDEX idx_job_postings_company_id ON job_postings(company_id);
CREATE INDEX idx_job_postings_location_id ON job_postings(location_id);
CREATE INDEX idx_job_postings_status ON job_postings(status);
CREATE INDEX idx_job_postings_created_at ON job_postings(created_at);
CREATE INDEX idx_job_postings_deadline_date ON job_postings(deadline_date);

-- 복합 인덱스
CREATE INDEX idx_job_postings_search 
ON job_postings(status, company_id, location_id);

-- 지원 관련 인덱스
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_posting_id ON applications(posting_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_applied_at ON applications(applied_at);

-- 복합 인덱스
CREATE INDEX idx_applications_user_posting 
ON applications(user_id, posting_id);

-- 북마크 관련 인덱스
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_posting_id ON bookmarks(posting_id);
CREATE INDEX idx_bookmarks_created_at ON bookmarks(created_at);

-- 기술스택 관련 인덱스
CREATE INDEX idx_tech_stacks_name ON tech_stacks(name);
CREATE INDEX idx_posting_tech_stacks_posting_id 
ON posting_tech_stacks(posting_id);
CREATE INDEX idx_posting_tech_stacks_stack_id 
ON posting_tech_stacks(stack_id);

-- 회사 관련 인덱스
CREATE INDEX idx_companies_name ON companies(name);

-- 위치 관련 인덱스
CREATE INDEX idx_locations_city ON locations(city);
CREATE INDEX idx_locations_district ON locations(district); 