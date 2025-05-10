#!/usr/bin/perl

use strict;
use warnings;
use Test::More;
use File::Spec;
use FindBin;
use Cwd 'abs_path';
use Log::Log4perl;
use File::Path 'make_path';

# Set up logging directory and file
my $log_dir  = File::Spec->catdir($FindBin::Bin, '..', 'logs');
my $log_file = File::Spec->catfile($log_dir, 'acme-frobnitz.log');

# Ensure log directory exists
unless (-d $log_dir) {
    eval { make_path($log_dir) };
    die "Failed to create log directory $log_dir: $@" if $@;
}

# Configure logging
my $log_config = qq(
log4perl.logger                         = INFO, Logfile

log4perl.appender.Logfile               = Log::Log4perl::Appender::File
log4perl.appender.Logfile.filename      = $log_file
log4perl.appender.Logfile.layout        = Log::Log4perl::Layout::PatternLayout
log4perl.appender.Logfile.layout.ConversionPattern = [%d] [%p] %m%n
);

Log::Log4perl->init(\$log_config);
my $logger = Log::Log4perl->get_logger();

# Load Frobnitz
use lib "$FindBin::Bin/../lib";
use Acme::Frobnitz;

my $frobnitz = Acme::Frobnitz->new();
my $test_url = 'https://www.instagram.com/p/DI1mHmsxllI/';  # Valid April 2024 link

$logger->info("🎬 Starting Acme::Frobnitz integration test");
can_ok('Acme::Frobnitz', 'download') or do {
    $logger->fatal("❌ 'download' method not found");
    BAIL_OUT("download method missing");
};

$logger->info("Using test URL: $test_url");

# Step 1: Download
my $output_file;
eval {
    $output_file = $frobnitz->download($test_url);
};
if ($@) {
    $logger->error("❌ Download failed: $@");
    fail("Download threw an exception");
} else {
    ok($output_file, "✅ Download completed");
    $logger->info("Download output: $output_file");
}

# Step 2: Verify downloaded file
my ($downloaded_file) = (split /\n/, $output_file)[-1];
chomp($downloaded_file);
if ($frobnitz->verify_file($downloaded_file)) {
    pass("✅ File verification passed");
    $logger->info("Verified downloaded file: $downloaded_file");
} else {
    fail("❌ File verification failed");
    $logger->fatal("Verification failed for file: $downloaded_file");
    BAIL_OUT("Stopping after failed verification");
}

# Step 3: Watermark
my $watermarked_file;
eval {
    $watermarked_file = $frobnitz->add_watermark($downloaded_file);
};
if ($@) {
    $logger->error("❌ Watermarking failed: $@");
    fail("Watermarking threw an exception");
} else {
    ok($watermarked_file, "✅ Watermarking completed");
    $logger->info("Watermarked file: $watermarked_file");
}

# Step 4: Verify watermarked file
if ($frobnitz->verify_file($watermarked_file)) {
    pass("✅ Watermarked file verification passed");
    $logger->info("Verified watermarked file: $watermarked_file");
} else {
    fail("❌ Watermarked file verification failed");
    $logger->fatal("Verification failed for watermarked file: $watermarked_file");
}

done_testing();

