import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from Project.models import AcademicProgram, ProgramComponent, ProgramCourse

class Command(BaseCommand):
    help = 'Import academic programs from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_dir',
            type=str,
            help='Directory containing program JSON files'
        )

    def handle(self, *args, **options):
        json_dir = options['json_dir']
        
        if not os.path.isdir(json_dir):
            self.stderr.write(self.style.ERROR(f"Directory does not exist: {json_dir}"))
            return

        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        
        if not json_files:
            self.stdout.write(self.style.WARNING("No JSON files found in directory"))
            return

        total_programs = 0
        total_courses = 0

        with transaction.atomic():
            for json_file in json_files:
                file_path = os.path.join(json_dir, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError as e:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping {json_file}: Invalid JSON format - {str(e)}"
                            ))
                            continue
                        
                        # Validate basic structure
                        if 'program' not in data:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping {json_file}: No 'program' key found at top level"
                            ))
                            continue
                            
                        program_data = data['program']

                        # Extract program year - more flexible handling
                        program_year = None
                        if 'year' in program_data:
                            program_year = str(program_data['year'])
                        else:
                            # Try to extract year from filename as fallback
                            try:
                                year_from_filename = ''.join(filter(str.isdigit, json_file))
                                if year_from_filename and len(year_from_filename) == 4:
                                    program_year = year_from_filename
                            except:
                                pass
                        
                        if not program_year:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping {json_file}: No 'year' field found and couldn't extract from filename"
                            ))
                            continue

                        # Create or update the program
                        try:
                            program, created = AcademicProgram.objects.update_or_create(
                                title=program_data.get('title', 'Unknown Program'),
                                year=program_year,
                                defaults={
                                    'total_credits': program_data.get('total_credits', 0)
                                }
                            )
                            total_programs += 1
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping {json_file}: Couldn't create program - {str(e)}"
                            ))
                            continue

                        # Process components if they exist
                        if 'components' in program_data and isinstance(program_data['components'], dict):
                            for comp_name, comp_data in program_data['components'].items():
                                try:
                                    # Extract component type (more robust)
                                    comp_type = ''.join([c for c in comp_name.split(' ')[0] if c.isalpha()])
                                    if not comp_type:
                                        comp_type = 'MR'  # Default to Major Requirement
                                    
                                    ProgramComponent.objects.update_or_create(
                                        program=program,
                                        component_type=comp_type,
                                        defaults={
                                            'credits': comp_data.get('credits', 0),
                                            'percentage': comp_data.get('percentage', '0%'),
                                            'notes': comp_data.get('note', comp_data.get('notes', ''))
                                        }
                                    )
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(
                                        f"Skipping component {comp_name} in {json_file}: {str(e)}"
                                    ))

                        # Process study plan if it exists
                        if 'study_plan' in program_data:
                            study_plan = program_data['study_plan']
                            
                            # Handle different study_plan formats
                            if isinstance(study_plan, dict):
                                # Standard format with years and semesters
                                self._process_study_plan_dict(program, study_plan, json_file)
                            elif isinstance(study_plan, list):
                                # Alternative format (like in Cy-2021.json)
                                self._process_study_plan_list(program, study_plan, json_file)
                            else:
                                self.stdout.write(self.style.WARNING(
                                    f"Skipping study_plan in {json_file}: Unexpected format"
                                ))

                except Exception as e:
                    self.stderr.write(self.style.ERROR(
                        f"Error processing {json_file}: {str(e)}"
                    ))
                    continue

        self.stdout.write(self.style.SUCCESS(
            f"\nImport completed:\n"
            f"Files processed: {len(json_files)}\n"
            f"Programs imported/updated: {total_programs}\n"
            f"Courses imported/updated: {total_courses}\n"
            f"\nNote: Some files may have been skipped due to format issues."
        ))

    def _process_study_plan_dict(self, program, study_plan, filename):
        """Process study plan in dictionary format (standard)"""
        course_count = 0
        for year_key, year_data in study_plan.items():
            try:
                # Extract year number
                if isinstance(year_key, str) and year_key.startswith('year_'):
                    year_num = int(year_key.split('_')[1])
                else:
                    year_num = 1  # Default to year 1 if can't determine
                
                if not isinstance(year_data, dict):
                    continue
                
                for sem_key, sem_courses in year_data.items():
                    try:
                        # Extract semester number
                        if isinstance(sem_key, str) and sem_key.startswith('semester_'):
                            sem_num = int(sem_key.split('_')[1])
                        else:
                            sem_num = 1  # Default to semester 1
                        
                        if not isinstance(sem_courses, list):
                            continue
                        
                        for course_data in sem_courses:
                            try:
                                self._create_course_record(program, course_data, year_num, sem_num)
                                course_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(
                                    f"Skipping course in {filename} (year {year_num}, semester {sem_num}): {str(e)}"
                                ))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"Skipping semester in {filename}: {str(e)}"
                        ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Skipping year in {filename}: {str(e)}"
                ))
        
        return course_count

    def _process_study_plan_list(self, program, study_plan, filename):
        """Process study plan in list format (alternative)"""
        course_count = 0
        for course_data in study_plan:
            try:
                # For list format, assume year 1 semester 1 unless specified
                year_num = course_data.get('year', 1)
                sem_num = course_data.get('semester', 1)
                self._create_course_record(program, course_data, year_num, sem_num)
                course_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Skipping course in {filename}: {str(e)}"
                ))
        
        return course_count

    def _create_course_record(self, program, course_data, year_num, sem_num):
        """Helper to create a course record with standardized data"""
        # Clean prerequisites
        prereq = course_data.get('prerequisite', '')
        if prereq in ('---', 'None', ''):
            prereq = ''
        
        # Handle major_gpa in different formats
        major_gpa = course_data.get('major_gpa', False)
        if isinstance(major_gpa, str):
            major_gpa = major_gpa.lower() in ('yes', 'true', '1')
        
        ProgramCourse.objects.update_or_create(
            program=program,
            course_code=course_data['course_code'],
            year=year_num,
            semester=sem_num,
            defaults={
                'course_title': course_data.get('course_title', ''),
                'lecture_hours': course_data.get('lecture_hours', 0),
                'practical_hours': course_data.get('practical_hours', 0),
                'credits': course_data.get('credits', 0),
                'course_type': course_data.get('course_type', 'MR'),
                'prerequisite': prereq,
                'major_gpa': major_gpa
            }
        )