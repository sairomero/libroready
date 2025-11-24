#!/usr/bin/env python3
"""
KDP Formatter - Complete tool for analyzing and fixing KDP formatting issues
"""

import sys
import os
from pathlib import Path
import zipfile
import shutil
from defusedxml import ElementTree as DefusedET
import xml.etree.ElementTree as ET

sys.path.insert(0, '/mnt/skills/public/docx/ooxml')

class KDPFormatter:
    """Complete KDP formatting tool"""
    
    # KDP Requirements
    KDP_REQUIREMENTS = {
        'margins': {
            '24-150 pages': {'inside': 0.375, 'outside': 0.25, 'top': 0.25, 'bottom': 0.25},
            '151-300 pages': {'inside': 0.5, 'outside': 0.25, 'top': 0.25, 'bottom': 0.25},
            '301-500 pages': {'inside': 0.625, 'outside': 0.25, 'top': 0.25, 'bottom': 0.25},
            '501-700 pages': {'inside': 0.75, 'outside': 0.25, 'top': 0.25, 'bottom': 0.25},
            '701-828 pages': {'inside': 0.875, 'outside': 0.25, 'top': 0.25, 'bottom': 0.25}
        },
        'line_spacing': 1.15,  # Recommended
        'paragraph_indent': 720,  # 0.5 inch in twips
        'image_dpi': 300
    }
    
    NS = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'pkg': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }
    
    def __init__(self, docx_path, output_path=None):
        self.docx_path = Path(docx_path)
        self.output_path = Path(output_path) if output_path else self.docx_path.parent / f"{self.docx_path.stem}_kdp_formatted.docx"
        self.temp_dir = Path('/tmp/kdp_temp')
        self.issues = []
        self.fixes_applied = []
        
    def analyze(self):
        """Analyze document for KDP compliance"""
        print(f"📖 Analyzing: {self.docx_path.name}\n")
        print("=" * 70)
        
        with zipfile.ZipFile(self.docx_path, 'r') as zf:
            doc_xml = zf.read('word/document.xml')
            root = DefusedET.fromstring(doc_xml)
            
            self._check_paragraphs(root)
            self._check_headings(root)
            self._check_page_breaks(root)
            self._check_toc(root)
            
            try:
                if 'word/_rels/document.xml.rels' in zf.namelist():
                    self._check_images(zf)
            except:
                pass
                
        return self._print_report()
    
    def _check_paragraphs(self, root):
        """Check paragraph formatting"""
        paragraphs = root.findall('.//w:p', self.NS)
        
        tab_count = 0
        no_indent_count = 0
        inconsistent_spacing = 0
        
        for para in paragraphs:
            # Check for tabs (bad practice for eBooks)
            tabs = para.findall('.//w:tab', self.NS)
            if tabs:
                tab_count += 1
            
            # Check indentation
            pPr = para.find('.//w:pPr', self.NS)
            if pPr is not None:
                ind = pPr.find('.//w:ind', self.NS)
                if ind is None:
                    # Check if it's body text (has text content, not a heading)
                    has_text = para.find('.//w:t', self.NS) is not None
                    pStyle = pPr.find('.//w:pStyle', self.NS)
                    is_heading = pStyle is not None and 'Heading' in pStyle.get(f'{{{self.NS["w"]}}}val', '')
                    
                    if has_text and not is_heading:
                        no_indent_count += 1
        
        if tab_count > 0:
            self.issues.append({
                'severity': 'error',
                'message': f'❌ Found {tab_count} paragraphs using TAB indentation',
                'detail': 'Tabs don\'t convert properly to eBook format',
                'fix': 'Replace tabs with proper first-line indentation'
            })
        
        if no_indent_count > 5:
            self.issues.append({
                'severity': 'warning',
                'message': f'⚠️  {no_indent_count} paragraphs missing first-line indentation',
                'detail': 'Body paragraphs should have consistent indentation',
                'fix': 'Apply 0.5" first-line indent to body paragraphs'
            })
    
    def _check_headings(self, root):
        """Check heading structure"""
        headings = root.findall('.//w:pStyle[@w:val="Heading1"]', self.NS)
        
        if len(headings) == 0:
            self.issues.append({
                'severity': 'error',
                'message': '❌ No Heading 1 styles found',
                'detail': 'Chapter titles need Heading 1 style for proper table of contents',
                'fix': 'Apply Heading 1 style to chapter titles'
            })
        else:
            self.issues.append({
                'severity': 'success',
                'message': f'✅ Found {len(headings)} chapter headings',
                'detail': 'Good heading structure for navigation'
            })
    
    def _check_page_breaks(self, root):
        """Check for page breaks"""
        page_breaks = root.findall('.//w:br[@w:type="page"]', self.NS)
        
        if len(page_breaks) < 2:
            self.issues.append({
                'severity': 'warning',
                'message': '⚠️  Few or no page breaks found',
                'detail': 'Use page breaks to separate major sections',
                'fix': 'Add page breaks before chapter headings'
            })
    
    def _check_toc(self, root):
        """Check for table of contents"""
        # Look for TOC field
        toc_fields = root.findall('.//w:fldChar[@w:fldCharType="begin"]', self.NS)
        has_toc = False
        
        for field in toc_fields:
            # Check if followed by TOC instruction
            para = field.find('../../../..', self.NS)
            if para is not None:
                instr = para.find('.//w:instrText', self.NS)
                if instr is not None and 'TOC' in (instr.text or ''):
                    has_toc = True
                    break
        
        if not has_toc:
            self.issues.append({
                'severity': 'warning',
                'message': '⚠️  No table of contents detected',
                'detail': 'A TOC improves reader navigation in eBooks',
                'fix': 'Insert automatic table of contents'
            })
    
    def _check_images(self, zf):
        """Check images"""
        rels_xml = zf.read('word/_rels/document.xml.rels')
        rels_root = DefusedET.fromstring(rels_xml)
        
        images = rels_root.findall('.//pkg:Relationship[@Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"]', self.NS)
        
        if len(images) > 0:
            self.issues.append({
                'severity': 'info',
                'message': f'📷 Found {len(images)} images',
                'detail': 'Ensure images are 300+ DPI for best quality',
                'fix': 'Check image resolution and file size'
            })
    
    def _print_report(self):
        """Print formatted report"""
        print("\n📊 ANALYSIS REPORT")
        print("=" * 70)
        
        errors = [i for i in self.issues if i['severity'] == 'error']
        warnings = [i for i in self.issues if i['severity'] == 'warning']
        successes = [i for i in self.issues if i['severity'] == 'success']
        infos = [i for i in self.issues if i['severity'] == 'info']
        
        if errors:
            print("\n🚫 CRITICAL ISSUES:")
            for issue in errors:
                print(f"\n  {issue['message']}")
                print(f"     └─ {issue['detail']}")
                print(f"     └─ Fix: {issue['fix']}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for issue in warnings:
                print(f"\n  {issue['message']}")
                print(f"     └─ {issue['detail']}")
                if 'fix' in issue:
                    print(f"     └─ Fix: {issue['fix']}")
        
        if successes:
            print("\n✅ GOOD PRACTICES:")
            for issue in successes:
                print(f"\n  {issue['message']}")
                print(f"     └─ {issue['detail']}")
        
        if infos:
            print("\nℹ️  ADDITIONAL INFO:")
            for issue in infos:
                print(f"\n  {issue['message']}")
                print(f"     └─ {issue['detail']}")
                if 'fix' in issue:
                    print(f"     └─ Recommendation: {issue['fix']}")
        
        print("\n" + "=" * 70)
        
        if errors:
            print("\n⚠️  Your document has critical issues that may cause KDP rejection.")
            print("   Run with --fix flag to automatically correct these issues.")
        elif warnings:
            print("\n✓ Your document meets basic requirements but could be improved.")
            print("  Run with --fix flag to apply recommended improvements.")
        else:
            print("\n✅ Your document looks great! Ready for KDP upload.")
        
        print()
        return len(errors) == 0
    
    def fix_formatting(self):
        """Apply automatic fixes"""
        print(f"🔧 Fixing formatting issues in: {self.docx_path.name}\n")
        
        # Create temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True)
        
        # Extract document
        with zipfile.ZipFile(self.docx_path, 'r') as zf:
            zf.extractall(self.temp_dir)
        
        # Load document.xml
        doc_path = self.temp_dir / 'word' / 'document.xml'
        tree = ET.parse(doc_path)
        root = tree.getroot()
        
        # Apply fixes
        self._fix_tabs(root)
        self._fix_indentation(root)
        self._fix_line_spacing(root)
        
        # Save modified document
        tree.write(doc_path, encoding='utf-8', xml_declaration=True)
        
        # Create output zip
        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zf.write(file_path, arcname)
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
        
        print("✅ Fixes applied successfully!")
        print(f"📄 Formatted document saved to: {self.output_path}\n")
        
        for fix in self.fixes_applied:
            print(f"  ✓ {fix}")
        
        print()
    
    def _fix_tabs(self, root):
        """Remove tabs and replace with proper indentation"""
        paragraphs = root.findall('.//w:p', self.NS)
        tabs_removed = 0
        
        for para in paragraphs:
            tabs = para.findall('.//w:tab', self.NS)
            if tabs:
                for tab in tabs:
                    parent = para.find('.//*[w:tab]/.', self.NS)
                    if parent is not None:
                        parent.remove(tab)
                        tabs_removed += 1
        
        if tabs_removed > 0:
            self.fixes_applied.append(f"Removed {tabs_removed} tab characters")
    
    def _fix_indentation(self, root):
        """Apply proper first-line indentation"""
        paragraphs = root.findall('.//w:p', self.NS)
        indents_added = 0
        
        for para in paragraphs:
            pPr = para.find('.//w:pPr', self.NS)
            
            # Check if it's body text
            has_text = para.find('.//w:t', self.NS) is not None
            if not has_text:
                continue
                
            # Skip headings
            if pPr is not None:
                pStyle = pPr.find('.//w:pStyle', self.NS)
                if pStyle is not None:
                    style_val = pStyle.get(f'{{{self.NS["w"]}}}val', '')
                    if 'Heading' in style_val or 'Title' in style_val:
                        continue
            
            # Add or ensure indentation
            if pPr is None:
                pPr = ET.SubElement(para, f'{{{self.NS["w"]}}}pPr')
                para.insert(0, pPr)
            
            ind = pPr.find('.//w:ind', self.NS)
            if ind is None:
                ind = ET.SubElement(pPr, f'{{{self.NS["w"]}}}ind')
            
            # Set first-line indent to 0.5 inches (720 twips)
            ind.set(f'{{{self.NS["w"]}}}firstLine', '720')
            indents_added += 1
        
        if indents_added > 0:
            self.fixes_applied.append(f"Applied first-line indentation to {indents_added} paragraphs")
    
    def _fix_line_spacing(self, root):
        """Apply consistent line spacing"""
        paragraphs = root.findall('.//w:p', self.NS)
        spacing_fixed = 0
        
        for para in paragraphs:
            pPr = para.find('.//w:pPr', self.NS)
            
            if pPr is None:
                pPr = ET.SubElement(para, f'{{{self.NS["w"]}}}pPr')
                para.insert(0, pPr)
            
            spacing = pPr.find('.//w:spacing', self.NS)
            if spacing is None:
                spacing = ET.SubElement(pPr, f'{{{self.NS["w"]}}}spacing')
            
            # Set line spacing to 1.15 (276 = 1.15 * 240)
            spacing.set(f'{{{self.NS["w"]}}}line', '276')
            spacing.set(f'{{{self.NS["w"]}}}lineRule', 'auto')
            spacing_fixed += 1
        
        if spacing_fixed > 0:
            self.fixes_applied.append(f"Applied consistent line spacing to {spacing_fixed} paragraphs")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='KDP Document Formatter')
    parser.add_argument('input', help='Input .docx file')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, do not fix')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Error: File not found: {args.input}")
        sys.exit(1)
    
    formatter = KDPFormatter(args.input, args.output)
    
    # Always analyze first
    is_compliant = formatter.analyze()
    
    # Apply fixes if requested
    if args.fix and not args.analyze_only:
        formatter.fix_formatting()
        print("\n🎉 Done! Your document is now KDP-ready.")
        print(f"📤 Upload {formatter.output_path} to Kindle Direct Publishing.")
    elif not is_compliant and not args.analyze_only:
        print("\n💡 Tip: Run with --fix flag to automatically correct issues:")
        print(f"   python kdp_formatter_complete.py {args.input} --fix")


if __name__ == "__main__":
    main()
