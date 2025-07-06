import json
import csv
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataOutput:
    """Handle data output in various formats"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def save_data(self, data: List[Dict[str, Any]], 
                  filename: str = None, 
                  format_type: str = "json",
                  include_timestamp: bool = True) -> str:
        """Save data in specified format"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"company_data_{timestamp}" if timestamp else "company_data"
        
        # Remove existing extension if present
        base_filename = os.path.splitext(filename)[0]
        
        if format_type.lower() == "json":
            return self._save_json(data, base_filename)
        elif format_type.lower() == "csv":
            return self._save_csv(data, base_filename)
        elif format_type.lower() in ["xlsx", "excel"]:
            return self._save_excel(data, base_filename)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _save_json(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Save data as JSON"""
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Data saved to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            raise
    
    def _save_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Save data as CSV"""
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        
        if not data:
            logger.warning("No data to save")
            return filepath
        
        try:
            # First flatten all records to get all possible fieldnames
            flattened_data = [self._flatten_record(record) for record in data]
            
            # Get all possible fieldnames from flattened records
            fieldnames = set()
            for record in flattened_data:
                fieldnames.update(record.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for flattened_record in flattened_data:
                    writer.writerow(flattened_record)
            
            logger.info(f"Data saved to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            raise
    
    def _save_excel(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Save data as Excel file"""
        filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
        
        if not data:
            logger.warning("No data to save")
            return filepath
        
        try:
            # Flatten data for Excel
            flattened_data = [self._flatten_record(record) for record in data]
            
            # Create DataFrame
            df = pd.DataFrame(flattened_data)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Company Data', index=False)
                
                # Summary sheet
                summary_data = self._generate_summary(data)
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Format sheets
                self._format_excel_sheets(writer, df, summary_df)
            
            logger.info(f"Data saved to Excel: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving Excel: {e}")
            raise
    
    def _flatten_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested dictionaries and lists for CSV/Excel export"""
        flattened = {}
        
        for key, value in record.items():
            if isinstance(value, dict):
                # Flatten dictionary
                for sub_key, sub_value in value.items():
                    flattened[f"{key}_{sub_key}"] = self._serialize_value(sub_value)
            elif isinstance(value, list):
                # Convert list to string
                flattened[key] = self._serialize_value(value)
            else:
                flattened[key] = self._serialize_value(value)
        
        return flattened
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize complex values to string"""
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        elif value is None:
            return ""
        else:
            return str(value)
    
    def _generate_summary(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate summary statistics"""
        if not data:
            return []
        
        summary = []
        
        # Basic stats
        summary.append({"Metric": "Total Companies", "Value": len(data)})
        
        # Count by extraction level
        levels = {}
        for record in data:
            level = record.get("extraction_level", "unknown")
            levels[level] = levels.get(level, 0) + 1
        
        for level, count in levels.items():
            summary.append({"Metric": f"Companies - {level.title()} Level", "Value": count})
        
        # Contact info availability
        email_count = sum(1 for record in data if record.get("email"))
        phone_count = sum(1 for record in data if record.get("phone"))
        address_count = sum(1 for record in data if record.get("address"))
        
        summary.append({"Metric": "Companies with Email", "Value": email_count})
        summary.append({"Metric": "Companies with Phone", "Value": phone_count})
        summary.append({"Metric": "Companies with Address", "Value": address_count})
        
        # Social media presence
        social_count = sum(1 for record in data if record.get("social_media"))
        summary.append({"Metric": "Companies with Social Media", "Value": social_count})
        
        # Tech stack info
        tech_count = sum(1 for record in data if record.get("tech_stack"))
        summary.append({"Metric": "Companies with Tech Stack Info", "Value": tech_count})
        
        return summary
    
    def _format_excel_sheets(self, writer, main_df, summary_df):
        """Format Excel sheets for better readability"""
        try:
            from openpyxl.styles import Font, Alignment, PatternFill
            from openpyxl.utils.dataframe import dataframe_to_rows
            
            # Format main sheet
            main_sheet = writer.sheets['Company Data']
            
            # Header formatting
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in main_sheet[1]:  # First row (headers)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in main_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                main_sheet.column_dimensions[column_letter].width = adjusted_width
            
            # Format summary sheet
            summary_sheet = writer.sheets['Summary']
            
            for cell in summary_sheet[1]:  # First row (headers)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust summary sheet column widths
            for column in summary_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = max_length + 2
                summary_sheet.column_dimensions[column_letter].width = adjusted_width
            
        except Exception as e:
            logger.warning(f"Could not format Excel sheets: {e}")
    
    def save_sample_data(self, data: List[Dict[str, Any]], 
                        sample_size: int = 5,
                        filename: str = "sample_data") -> List[str]:
        """Save sample data in all formats"""
        if not data:
            logger.warning("No data to save sample from")
            return []
        
        sample_data = data[:sample_size]
        saved_files = []
        
        for format_type in ["json", "csv", "xlsx"]:
            try:
                filepath = self.save_data(sample_data, f"{filename}_sample", format_type)
                saved_files.append(filepath)
            except Exception as e:
                logger.error(f"Error saving sample in {format_type}: {e}")
        
        return saved_files
    
    def load_data(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_extension = os.path.splitext(filepath)[1].lower()
        
        if file_extension == ".json":
            return self._load_json(filepath)
        elif file_extension == ".csv":
            return self._load_csv(filepath)
        elif file_extension in [".xlsx", ".xls"]:
            return self._load_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _load_json(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            else:
                return [data]
                
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            raise
    
    def _load_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        try:
            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def _load_excel(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from Excel file"""
        try:
            df = pd.read_excel(filepath, sheet_name='Company Data')
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            raise
    
    def get_output_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the output data"""
        if not data:
            return {"total_companies": 0}
        
        stats = {
            "total_companies": len(data),
            "extraction_levels": {},
            "data_completeness": {},
            "contact_info_availability": {},
            "social_media_presence": 0,
            "tech_stack_info": 0
        }
        
        # Count by extraction level
        for record in data:
            level = record.get("extraction_level", "unknown")
            stats["extraction_levels"][level] = stats["extraction_levels"].get(level, 0) + 1
        
        # Data completeness
        required_fields = ["company_name", "website_url", "email", "phone"]
        for field in required_fields:
            complete_count = sum(1 for record in data if record.get(field))
            stats["data_completeness"][field] = {
                "count": complete_count,
                "percentage": (complete_count / len(data)) * 100
            }
        
        # Contact info availability
        stats["contact_info_availability"] = {
            "email": sum(1 for record in data if record.get("email")),
            "phone": sum(1 for record in data if record.get("phone")),
            "address": sum(1 for record in data if record.get("address"))
        }
        
        # Social media and tech stack
        stats["social_media_presence"] = sum(1 for record in data if record.get("social_media"))
        stats["tech_stack_info"] = sum(1 for record in data if record.get("tech_stack"))
        
        return stats 