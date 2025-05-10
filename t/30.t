#!/usr/bin/perl

use strict;
use warnings;
use Test::More;
use File::Spec;
use FindBin;
use Log::Log4perl;
use File::Path 'make_path';
use Acme::Frobnitz;
use Time::HiRes qw(sleep);  # For adding a small delay
use File::Basename;         # For extracting file name components

# Set up logging
my $log_dir = File::Spec->catdir($FindBin::Bin, '..', 'logs');
my $log_file = File::Spec->catfile($log_dir, 'acme-frobnitz.log');

unless (-d $log_dir) {
    eval { make_path($log_dir) };
    die "Failed to create log directory $log_dir: $@" if $@;
}

my $log_config = qq(
log4perl.logger = INFO, FileAppender
log4perl.appender.FileAppender = Log::Log4perl::Appender::File
log4perl.appender.FileAppender.filename = $log_file
log4perl.appender.FileAppender.layout = Log::Log4perl::Layout::PatternLayout
log4perl.appender.FileAppender.layout.ConversionPattern = %d [%p] %m%n
);
Log::Log4perl->init(\$log_config);
my $logger = Log::Log4perl->get_logger();

# Instantiate Frobnitz object
my $frobnitz = Acme::Frobnitz->new();

# Define a test video URL
#my $video_url = 'https://www.youtube.com/watch?v=1udSWwkEQV0'; # _Visions of Glory_ Word Wise...Kitt
my $video_url = 'https://www.youtube.com/watch?v=7Yhnml4DW9g'; # bern

$logger->info("Starting test for video processing pipeline");
$logger->info("Downloading video from: $video_url");

# Step 1: Download Video
my $downloaded_file = $frobnitz->download($video_url);
$logger->info("DEBUG: Raw filename before cleanup -> '$downloaded_file'");
print "DEBUG: Raw filename before cleanup -> '$downloaded_file'\n";

# Trim spaces/newlines from filename
chomp($downloaded_file);
$downloaded_file =~ s/^\s+|\s+$//g;  # Trim spaces/newlines

# Log cleaned path
$logger->info("Downloaded file: '$downloaded_file'");
print "DEBUG: Downloaded file -> '$downloaded_file'\n";

# Ensure file exists
if (!-e $downloaded_file) {
    die "ERROR: Download failed. No such file: '$downloaded_file'\n";
}
ok(-e $downloaded_file, "Downloaded video file exists: $downloaded_file");

# Step 2: Apply Watermark
my $watermarked_file = $frobnitz->add_watermark($downloaded_file);
chomp($watermarked_file);
print "DEBUG: Watermarked file -> '$watermarked_file'\n";
$logger->info("Watermarked video file: $watermarked_file");

# Wait a bit longer to ensure the file is fully written
sleep(5);  # Give MoviePy more time to finish writing the file

# Verify Watermarked File
# Check if there's any special characters or unexpected whitespace in the file path
print "DEBUG: Checking if watermarked file exists at: '$watermarked_file'\n";

# Use `ls -l` to check file permissions and existence
my $file_check = `ls -l "$watermarked_file"`;
print "DEBUG: File check output: $file_check\n";

# Check if file exists and permissions
if (!-e $watermarked_file) {
    die "ERROR: Watermark failed. No such file: '$watermarked_file'\n";
}

ok(-e $watermarked_file, "Watermarked video file exists: $watermarked_file");

# Step 3: Extract Clips
my $yaml_file = "";
my $clips_file = $frobnitz->make_clips($watermarked_file, $yaml_file);
chomp($clips_file);
print "DEBUG: Clips file -> '$clips_file'\n";
$logger->info("Clips file generated: $clips_file");

# Verify Clips File
if (!-e $clips_file) {
    die "ERROR: Clips extraction failed. No such file: '$clips_file'\n";
}
ok(-e $clips_file, "Clips extracted successfully: $clips_file");

$logger->info("Test pipeline completed successfully.");
done_testing();
